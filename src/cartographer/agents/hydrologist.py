# src/cartographer/agents/hydrologist.py
from pathlib import Path
from typing import List, Dict
import subprocess
from datetime import datetime, timedelta

from src.cartographer.graph.knowledge_graph import KnowledgeGraph
from src.cartographer.analyzers.tree_sitter_analyzer import TreeSitterAnalyzer

EXCLUDED_DIRS = {"venv", "env", "node_modules", "build", "dist", "__pycache__"}

class Hydrologist:
    """Data Lineage Agent: Maps how data flows between datasets."""

    def __init__(self, kg: KnowledgeGraph, ts_analyzer: TreeSitterAnalyzer):
        self.kg = kg
        self.ts_analyzer = ts_analyzer

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

    def _analyze_sql_lineage(self, file_path: Path):
        """
        In dbt/SQL projects, the filename is the target table.
        The 'imports' found by the Surveyor are the source tables.
        """
        target_dataset = file_path.stem  # e.g., 'stg_customers'
        str_path = str(file_path)

        # 1. Register the target dataset
        self.kg.add_dataset(target_dataset, storage_type="table")

        # 2. Get dependencies already found by Surveyor in the module_graph
        module_data = self.kg.module_graph.nodes.get(str_path, {})
        sources = module_data.get("imports", [])

        for source in sources:
            # Add source dataset to lineage graph
            self.kg.add_dataset(source, storage_type="table")

            # Create the directed edge: Source -> Target
            # Using your LineageEdge model logic (Source produces Target)
            self.kg.add_lineage_edge(
                source=source,
                target=target_dataset,
                edge_type="PRODUCES"
            )

    def _analyze_python_dataflow(self, file_path: Path):
        """Standard AST check for pandas/spark style read/writes."""
        tree = self.ts_analyzer.get_tree(str(file_path))
        if not tree:
            return

        # Target calls often indicating data movement
        TARGET_CALLS = {"read_csv", "read_sql", "to_csv", "to_sql", "execute"}

        # This uses the tree to find function calls (Simplified logic)
        def walk(node):
            if node.type == "call":
                # Logic to extract the dataset name from the first argument
                # Similar to your previous PythonDataFlowAnalyzer
                pass
            for child in node.children:
                walk(child)

        walk(tree.root_node)

    def _analyze_yaml_sources(self, file_path: Path):
        """Identify raw sources defined in dbt/config YAMLs."""
        # Raw sources act as the 'root' of your lineage graph
        if "schema" in file_path.name or "sources" in file_path.name:
            # Logic to extract source names from YAML
            # and add them via self.kg.add_dataset(source_name)
            pass

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
