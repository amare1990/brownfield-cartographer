# src/cartographer/agents/hydrologist.py
from pathlib import Path
from typing import List, Dict
import subprocess
from datetime import datetime, timedelta

from src.cartographer.graph.knowledge_graph import KnowledgeGraph
from src.cartographer.analyzers.sql_lineage import SQLLineageAnalyzer
from src.cartographer.analyzers.dag_config_parser import DAGConfigAnalyzer

from tree_sitter import Language, Parser


# ----- Git velocity for Python files -----
def extract_git_velocity(repo_path: str, days: int = 30) -> Dict[str, int]:
    """Compute commit frequency per Python file over the last `days` in the Git repository."""
    repo_path_obj = Path(repo_path)
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    file_commit_counts: Dict[str, int] = {}

    py_files = [f for f in repo_path_obj.rglob("*.py") if f.is_file()]
    for file_path in py_files:
        try:
            result = subprocess.run(
                ["git", "log", "--since", since_date, "--follow", "--pretty=format:%H", str(file_path)],
                cwd=str(repo_path_obj),
                capture_output=True,
                text=True,
                check=True,
            )
            file_commit_counts[str(file_path)] = len(result.stdout.splitlines())
        except subprocess.CalledProcessError:
            continue

    return file_commit_counts


class PythonDataFlowAnalyzer:
    """Python dataflow analyzer using Tree-sitter AST traversal."""

    TARGET_CALLS = {"read_csv", "read_sql", "execute", "read", "write"}

    def __init__(self, kg: KnowledgeGraph, parser: Parser):
        self.kg = kg
        self.parser = parser

    def analyze_file(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            code_bytes = f.read().encode("utf-8")
        tree = self.parser.parse(code_bytes)
        self._walk_node(tree.root_node, code_bytes, file_path)

    def _walk_node(self, node, code_bytes, file_path: str):
        if node.type == "call":
            func_node = node.child_by_field_name("function")
            if func_node:
                func_name = self._get_func_name(func_node, code_bytes)
                if func_name.split(".")[-1] in self.TARGET_CALLS:
                    dataset_name = self._extract_first_arg(node, code_bytes)
                    # Add dataset to KnowledgeGraph
                    self.kg.add_dataset(dataset_name)
                    # Add optional metadata: source file
                    self.kg.lineage_graph.nodes[dataset_name]["source_file"] = str(file_path)
        for child in node.children:
            self._walk_node(child, code_bytes, file_path)

    def _get_func_name(self, node, code_bytes) -> str:
        if node.type == "identifier":
            return code_bytes[node.start_byte:node.end_byte].decode("utf-8")
        elif node.type == "attribute":
            parts = [code_bytes[c.start_byte:c.end_byte].decode("utf-8") for c in node.children if c.type != "."]
            return ".".join(parts)
        return "unknown"

    def _extract_first_arg(self, call_node, code_bytes) -> str:
        arg_node = call_node.child_by_field_name("arguments")
        if arg_node and len(arg_node.children) > 0:
            return code_bytes[arg_node.children[0].start_byte:arg_node.children[0].end_byte].decode("utf-8")
        return "dynamic reference, cannot resolve"


class Hydrologist:
    """Data Lineage Agent integrating Python, SQL, and DAG config analyzers."""

    def __init__(self, kg: KnowledgeGraph, python_parser: Parser):
        self.kg = kg
        self.python_analyzer = PythonDataFlowAnalyzer(kg, python_parser)
        self.sql_analyzer = SQLLineageAnalyzer(kg)
        self.dag_analyzer = DAGConfigAnalyzer()

    def analyze_repo(self, repo_path: str):
        """Analyze all files in a repo and populate lineage graph with optional git velocity."""
        repo_path_obj = Path(repo_path)

        # Compute Python file velocity
        velocity_map = extract_git_velocity(repo_path)

        for file_path in repo_path_obj.rglob("*"):
            if not file_path.is_file():
                continue
            ext = file_path.suffix.lower()
            if ext == ".py":
                self.python_analyzer.analyze_file(str(file_path))
                # Attach velocity to each dataset produced from this file
                for dataset, attrs in self.kg.lineage_graph.nodes(data=True):
                    if attrs.get("source_file") == str(file_path):
                        self.kg.lineage_graph.nodes[dataset]["change_velocity_30d"] = velocity_map.get(str(file_path), 0)
            elif ext == ".sql":
                with open(file_path, "r", encoding="utf-8") as f:
                    sql_text = f.read()
                self.sql_analyzer.analyze_sql_file(str(file_path), sql_text)
            elif ext in {".yml", ".yaml"}:
                self.dag_analyzer.parse_dbt_schema(str(file_path))
                self.dag_analyzer.parse_airflow_dag(str(file_path))

        return self.kg

    # ----- Utility methods for the lineage graph -----
    def blast_radius(self, node: str) -> List[str]:
        return list(self.kg.blast_radius(node))

    def find_sources(self) -> List[str]:
        return self.kg.find_sources()

    def find_sinks(self) -> List[str]:
        return self.kg.find_sinks()
