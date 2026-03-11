# src/cartographer/agents/surveyor.py
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

from src.cartographer.graph.knowledge_graph import KnowledgeGraph
from src.cartographer.models.node import ModuleNode
import networkx as nx

from tree_sitter import Language, Parser

# ----- Git velocity -----
def extract_git_velocity(repo_path: str, days: int = 30) -> Dict[str, int]:
    """Compute commit frequency per file over the last `days` in the Git repository."""
    repo_path_obj = Path(repo_path)
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    file_commit_counts: Dict[str, int] = {}

    files = [f for f in repo_path_obj.rglob("*") if f.is_file()]
    for file_path in files:
        try:
            result = subprocess.run(
                ["git", "log", "--since", since_date, "--follow", "--pretty=format:%H", str(file_path)],
                cwd=str(repo_path_obj),
                capture_output=True,
                text=True,
                check=True
            )
            file_commit_counts[str(file_path)] = len(result.stdout.splitlines())
        except subprocess.CalledProcessError:
            continue

    if file_commit_counts:
        sorted_files = sorted(file_commit_counts.items(), key=lambda x: x[1], reverse=True)
        top_20pct_index = max(1, len(sorted_files) * 20 // 100)
        high_velocity_files = {f: c for f, c in sorted_files[:top_20pct_index]}
        for f, c in sorted_files[top_20pct_index:]:
            high_velocity_files[f] = c
        return high_velocity_files
    return {}

# ----- Tree-sitter Setup -----
PARSERS_PATH = Path(__file__).parent / "parsers.so"
PY_LANGUAGE = Language(str(PARSERS_PATH), "python")  # type: ignore
PARSER: Parser = Parser()  # type: ignore
PARSER.set_language(PY_LANGUAGE)  # type: ignore


class Surveyor:
    """Static structure analyzer using module imports and AST."""

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg

    def analyze_module(self, file_path: str) -> ModuleNode:
        """
        Parse a Python module using Tree-sitter, extract:
        - imports
        - public functions
        - classes
        Add nodes & edges to KnowledgeGraph.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            code_bytes = f.read().encode("utf-8")

        tree = PARSER.parse(code_bytes)
        root_node = tree.root_node

        imports: List[str] = []
        public_functions: List[str] = []
        classes: List[str] = []

        for node in root_node.children:
            if node.type in {"import_statement", "import_from_statement"}:
                for child in node.children:
                    if child.type == "dotted_name":
                        imp_name = code_bytes[child.start_byte:child.end_byte].decode("utf-8")
                        imports.append(imp_name)
                        self.kg.add_import(file_path, imp_name)

            elif node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    func_name = code_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8")
                    if not func_name.startswith("_"):
                        public_functions.append(func_name)
                        self.kg.add_module(func_name)
                        self.kg.add_import(file_path, func_name)

            elif node.type == "class_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    class_name = code_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8")
                    classes.append(class_name)
                    self.kg.add_module(class_name)
                    self.kg.add_import(file_path, class_name)

        # Add the module itself
        self.kg.add_module(file_path, attrs={
            "public_functions": public_functions,
            "classes": classes,
            "imports": imports,
        })

        return ModuleNode(
            path=file_path,
            language="python",
            purpose_statement=None,
            domain_cluster=None,
            complexity_score=None,
            change_velocity_30d=None,
            is_dead_code_candidate=False,
            last_modified=None
        )

    def analyze_repo(self, repo_path: str):
        """Walk repo, analyze all Python files, add git velocity info."""
        repo_path_obj = Path(repo_path)
        py_files = [f for f in repo_path_obj.rglob("*.py") if f.is_file()]

        velocity_map = extract_git_velocity(repo_path)

        for file_path in py_files:
            self.analyze_module(str(file_path))
            if str(file_path) in velocity_map:
                self.kg.module_graph.nodes[str(file_path)]["change_velocity_30d"] = velocity_map[str(file_path)]

        return self.kg

    def compute_pagerank(self):
        pr = nx.pagerank(self.kg.module_graph)
        for module, score in pr.items():
            print(module, score)
        return pr

    def strongly_connected_components(self):
        return list(nx.strongly_connected_components(self.kg.module_graph))
