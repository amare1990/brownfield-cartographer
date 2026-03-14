# src/cartographer/agents/hydrologist.py
from pathlib import Path
from typing import List, Union
import re
import yaml

from sqlglot import parse_one, exp

from src.cartographer.models.lineage import EdgeType
from src.cartographer.graph.knowledge_graph import KnowledgeGraph
from src.cartographer.analyzers.tree_sitter_analyzer import TreeSitterAnalyzer

EXCLUDED_DIRS = {"venv", "env", "node_modules", "build", "dist", "__pycache__"}

class Hydrologist:
    """Data Lineage Agent: Maps how data flows between datasets across multiple dialects."""

    def __init__(self, kg: KnowledgeGraph, ts_analyzer: TreeSitterAnalyzer, sql_dialect: str = "postgres"):
        self.kg = kg
        self.ts_analyzer = ts_analyzer
        self.sql_dialect = sql_dialect
        self.lineage_edges = []  # temporary storage before merging

    # ----------------------------
    # Main Repo Analysis
    # ----------------------------
    def analyze_repo(self, repo_path: str):
        """Populate the lineage graph from SQL, Python, YAML, and DAGs."""
        repo_path_obj = Path(repo_path)
        for file_path in repo_path_obj.rglob("*"):
            if any(part in EXCLUDED_DIRS for part in file_path.parts) or not file_path.is_file():
                continue

            ext = file_path.suffix.lower()
            if ext == ".sql":
                self._analyze_sql_lineage(file_path)
            elif ext == ".py":
                self._analyze_python_dataflow(file_path)
            elif ext in {".yml", ".yaml"}:
                self._analyze_yaml_sources(file_path)

        # Merge all collected edges into the lineage graph
        self._merge_edges()

    # ----------------------------
    # SQL Analysis
    # ----------------------------
    def _analyze_sql_lineage(self, file_path: Path):
        target_dataset = file_path.stem
        self.kg.add_dataset(target_dataset, storage_type="table")

        try:
            sql_text = file_path.read_text(encoding="utf-8")
            tree = parse_one(sql_text, read=self.sql_dialect)
        except Exception:
            # fallback: use imported modules as sources
            module_data = self.kg.module_graph.nodes.get(str(file_path), {})
            sources = module_data.get("imports", [])
            for src in sources:
                self._add_edge(src, target_dataset, EdgeType.PRODUCES, {"dialect": "unknown", "file": str(file_path)})
            return

        source_tables = [t.name for t in tree.find_all(exp.Table)]
        edge_type = self._determine_sql_edge_type(tree)

        for src in source_tables:
            self._add_edge(
                src,
                target_dataset,
                edge_type,
                self._edge_metadata(file_path, tree, "sql_select", dialect=self.sql_dialect)
            )

    def _determine_sql_edge_type(self, tree) -> EdgeType:
        if tree.find(exp.Create) or tree.find(exp.Insert):
            return EdgeType.PRODUCES
        if tree.find(exp.Select):
            return EdgeType.CONSUMES
        return EdgeType.PRODUCES

    # ----------------------------
    # Python Analysis
    # ----------------------------
    def _analyze_python_dataflow(self, file_path: Path):
        text = file_path.read_text()
        if "DAG(" in text:
            self._analyze_airflow_dag(file_path, text)

        tree = self.ts_analyzer.get_tree(str(file_path))
        if not tree:
            return

        TARGET_CALLS = {"read_csv", "read_sql", "to_csv", "to_sql"}

        def walk(node):
            if node.type == "call":
                func_name_node = node.child_by_field_name("function")
                if func_name_node:
                    func_name = func_name_node.text.decode("utf-8") if hasattr(func_name_node.text, "decode") else str(func_name_node.text)
                    args = [c.text.decode("utf-8") if hasattr(c, "text") else str(c) for c in node.children]

                    if func_name in {"read_csv", "read_sql"} and args:
                        dataset = args[0].strip('"\'')
                        self.kg.add_dataset(dataset, storage_type="file" if dataset.endswith(".csv") else "table")
                        self._add_edge(dataset, file_path.stem, EdgeType.CONSUMES, {"dialect": "python"})
                    elif func_name in {"to_csv", "to_sql"} and args:
                        dataset = args[0].strip('"\'')
                        self.kg.add_dataset(dataset, storage_type="file" if dataset.endswith(".csv") else "table")
                        self._add_edge(file_path.stem, dataset, EdgeType.PRODUCES, {"dialect": "python"})
                    else:
                        self._add_edge(file_path.stem, func_name, EdgeType.CALLS, {"dialect": "python"})

            for child in getattr(node, "children", []):
                walk(child)

        walk(tree.root_node)

    # ----------------------------
    # YAML Analysis
    # ----------------------------
    def _analyze_yaml_sources(self, file_path: Path):
        try:
            content = yaml.safe_load(file_path.read_text(encoding="utf-8"))
        except Exception:
            return

        if not content:
            return

        for key, items in content.items():
            if isinstance(items, list):
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    name = item.get("name")
                    if not name:
                        continue
                    storage_type = "table" if key in {"sources", "models"} else "file"
                    self.kg.add_dataset(name, storage_type=storage_type)
                    edge_type = EdgeType.CONFIGURES if key == "sources" else EdgeType.PRODUCES
                    self._add_edge(str(file_path), name, edge_type, {"yaml_key": key, "dialect": "yaml"})

    # ----------------------------
    # Airflow DAG Analysis
    # ----------------------------
    def _analyze_airflow_dag(self, file_path: Path, text: str):
        pattern = r"(\w+)\s*>>\s*(\w+)"
        matches = re.findall(pattern, text)
        for upstream, downstream in matches:
            self._add_edge(upstream, downstream, EdgeType.PRODUCES, {"type": "airflow_dependency", "dialect": "python"})

    # ----------------------------
    # Edge Handling
    # ----------------------------
    def _add_edge(self, source: str, target: str, edge_type: EdgeType, metadata: dict):
        """Add or merge edge to temporary list for later merging."""
        edge = {"source": source, "target": target, "edge_type": edge_type, "metadata": metadata}
        self.lineage_edges.append(edge)

    def _merge_edges(self):
        """Merge edges to ensure cross-language consistency and avoid duplicates."""
        merged = {}
        for edge in self.lineage_edges:
            key = (edge["source"], edge["target"])
            if key not in merged:
                merged[key] = edge
            else:
                existing = merged[key]
                # merge metadata
                existing_meta = existing["metadata"]
                for k, v in edge["metadata"].items():
                    if k not in existing_meta:
                        existing_meta[k] = v
                    elif isinstance(existing_meta[k], list):
                        existing_meta[k] = list(set(existing_meta[k] + ([v] if not isinstance(v, list) else v)))
                    else:
                        existing_meta[k] = list(set([existing_meta[k]] + ([v] if not isinstance(v, list) else v)))
        # push merged edges into graph
        for edge in merged.values():
            self.kg.add_lineage_edge(
                edge["source"], edge["target"], edge["edge_type"], metadata=edge["metadata"]
            )

    # ----------------------------
    # Metadata Helper
    # ----------------------------
    def _edge_metadata(self, file_path, node=None, transform=None, dialect="sql"):
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
            "transformation": transform,
            "dialect": dialect
        }

    # ----------------------------
    # Lineage Queries
    # ----------------------------
    def blast_radius(self, node: str) -> List[str]:
        return list(self.kg.blast_radius(node))

    def find_sources(self) -> List[str]:
        return self.kg.find_sources()

    def find_sinks(self) -> List[str]:
        return self.kg.find_sinks()
