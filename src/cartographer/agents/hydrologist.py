# src/cartographer/agents/hydrologist.py
from pathlib import Path
from typing import List

import re
import yaml

from sqlglot import parse_one, exp

from src.cartographer.models.lineage import EdgeType
from src.cartographer.graph.knowledge_graph import KnowledgeGraph
from src.cartographer.analyzers.tree_sitter_analyzer import TreeSitterAnalyzer

EXCLUDED_DIRS = {"venv", "env", "node_modules", "build", "dist", "__pycache__"}

class Hydrologist:
    """Data Lineage Agent: Maps how data flows between datasets."""

    def __init__(self, kg: KnowledgeGraph, ts_analyzer: TreeSitterAnalyzer, sql_dialect: str = "postgres"):
        self.kg = kg
        self.ts_analyzer = ts_analyzer
        self.sql_dialect = sql_dialect

    def analyze_repo(self, repo_path: str):
        """
        Populate the lineage graph by bridging module dependencies
        to data transformations.
        """
        repo_path_obj = Path(repo_path)

        # Iterate through files to identify 'Datasets' and 'Transformations'
        for file_path in repo_path_obj.rglob("*"):
            if any(part in EXCLUDED_DIRS for part in file_path.parts) or not file_path.is_file():
                continue

            ext = file_path.suffix.lower()
            str_path = str(file_path)

            if ext == ".sql":
                self._analyze_sql_lineage(file_path)
            elif ext == ".py":
                self._analyze_python_dataflow(file_path)
            elif ext in {".yml", ".yaml"}:
                self._analyze_yaml_sources(file_path)

    # sqlglot-based SQL lineage analysis
    def _analyze_sql_lineage(self, file_path: Path):
        target_dataset = file_path.stem
        self.kg.add_dataset(target_dataset, storage_type="table")

        try:
            sql_text = file_path.read_text(encoding="utf-8")
            tree = parse_one(sql_text, read=self.sql_dialect)
        except Exception:
            # fallback: treat all imported modules as sources
            module_data = self.kg.module_graph.nodes.get(str(file_path), {})
            sources = module_data.get("imports", [])
            for source in sources:
                self.kg.add_dataset(source, storage_type="table")
                self.kg.add_lineage_edge(
                    source=source,
                    target=target_dataset,
                    edge_type=EdgeType.PRODUCES,
                    metadata=self._edge_metadata(file_path, None, "sql_select"),
                )
            return

        # Extract tables used in FROM/JOIN/CTEs
        source_tables = [t.name for t in tree.find_all(exp.Table)]

        # Determine edge type based on statement type
        if tree.find(exp.Create):
            edge_type = EdgeType.PRODUCES
        elif tree.find(exp.Insert):
            edge_type = EdgeType.PRODUCES
        elif tree.find(exp.Select):
            edge_type = EdgeType.CONSUMES
        else:
            edge_type = EdgeType.PRODUCES


        # Add edges for sources
        for src in source_tables:
            self.kg.add_dataset(src, storage_type="table")
            self.kg.add_lineage_edge(
                source=src,
                target=target_dataset,
                edge_type=edge_type,
                metadata=self._edge_metadata(file_path, None, "sql_select")

            )

    def _analyze_python_dataflow(self, file_path: Path):

        text = file_path.read_text()

        if "DAG(" in text:
            self._analyze_airflow_dag(file_path, text)


        tree = self.ts_analyzer.get_tree(str(file_path))
        if not tree:
            return

        # TARGET_CALLS = {"read_csv", "read_sql", "to_csv", "to_sql", "execute"}
        TARGET_CALLS = {"read_csv", "read_sql", "to_csv", "to_sql"}


        def walk(node):
            if node.type == "call":
                func_name_node = node.child_by_field_name("function")
                if func_name_node:
                    func_name = func_name_node.text.decode("utf-8") if hasattr(func_name_node.text, 'decode') else str(func_name_node.text)
                    args = [
                        c.text.decode("utf-8")
                        for c in node.children
                        if hasattr(c, "text")
                    ]

                    if func_name in {"read_csv", "read_sql"} and args:
                        dataset = args[0].strip('"\'')
                        self.kg.add_dataset(dataset, storage_type="file" if dataset.endswith(".csv") else "table")
                        self.kg.add_lineage_edge(
                            source=dataset,
                            target=file_path.stem,
                            edge_type=EdgeType.CONSUMES
                        )
                    elif func_name in {"to_csv", "to_sql"} and args:
                        dataset = args[0].strip('"\'')
                        self.kg.add_dataset(dataset, storage_type="file" if dataset.endswith(".csv") else "table")
                        self.kg.add_lineage_edge(
                            source=file_path.stem,
                            target=dataset,
                            edge_type=EdgeType.PRODUCES
                        )
                    else:
                        # generic function call
                        self.kg.add_lineage_edge(
                            source=file_path.stem,
                            target=func_name,
                            edge_type=EdgeType.CALLS
                        )
            for child in getattr(node, 'children', []):
                walk(child)

        walk(tree.root_node)

    # YAML-based source/model extraction
    def _analyze_yaml_sources(self, file_path: Path):
        """
        Parse dbt-style YAML files to extract source datasets, tables, and configurations.
        Add them to the lineage graph with proper edge types.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
        except Exception:
            return  # skip bad YAML

        if not content:
            return

        # Detect sources, models, and configs
        for key in content:
            items = content.get(key)
            if isinstance(items, list):
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    name = item.get("name")
                    if not name:
                        continue

                    # Decide storage type: tables or files
                    storage_type = "table" if key in {"sources", "models"} else "file"

                    # Register dataset
                    self.kg.add_dataset(name, storage_type=storage_type)

                    # Create edges: CONFIGURES for configs, PRODUCES for models
                    if key == "sources":
                        edge_type = EdgeType.CONFIGURES
                    else:
                        edge_type = EdgeType.PRODUCES

                    self.kg.add_lineage_edge(
                        source=str(file_path),  # config file is the source
                        target=name,
                        edge_type=edge_type,
                        metadata={
                            "source_file": str(file_path),
                            "yaml_key": key
                        }
                    )

    # Helper to extract metadata for edges
    def _edge_metadata(self, file_path, node=None, transform=None):
        if isinstance(node, exp.Join):
            transform = "join"
        elif isinstance(node, exp.Group):
            transform = "aggregation"
        elif isinstance(node, exp.Where):
            transform = "filter"
        elif isinstance(node, exp.Func) and getattr(node, "is_aggregate", False):
            transform = "aggregation"

        return {
            "file": str(file_path),
            "line_start": getattr(node, "line", None),
            "line_end": getattr(node, "end_line", None),
            "transformation": transform
        }


    def _analyze_airflow_dag(self, file_path: Path, text: str):

        pattern = r"(\w+)\s*>>\s*(\w+)"
        matches = re.findall(pattern, text)

        for upstream, downstream in matches:
            self.kg.add_lineage_edge(
                source=upstream,
                target=downstream,
                edge_type=EdgeType.PRODUCES,
                metadata={"file": str(file_path), "type": "airflow_dependency"}
            )

    def add_merged_edge(self, source, target, edge_type, metadata):
        existing = self.kg.lineage_graph.get_edge_data(source, target)

        if existing:
            existing["metadata"].update(metadata)
        else:
            self.kg.add_lineage_edge(source, target, edge_type=edge_type, metadata=metadata)


    # ----- Lineage Queries -----
    def blast_radius(self, node: str) -> List[str]:
        """Which downstream datasets are affected if this node changes?"""
        return list(self.kg.blast_radius(node))

    def find_sources(self) -> List[str]:
        """Find datasets with no upstream dependencies."""
        return self.kg.find_sources()

    def find_sinks(self) -> List[str]:
        """Find datasets with no downstream dependencies."""
        return self.kg.find_sinks()
