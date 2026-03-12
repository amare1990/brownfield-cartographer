# src/cartographer/agents/surveyor.py
import subprocess
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

from src.cartographer.graph.knowledge_graph import KnowledgeGraph
from src.cartographer.models.node import ModuleNode
from src.cartographer.analyzers.tree_sitter_analyzer import TreeSitterAnalyzer
import networkx as nx

EXCLUDED_DIRS = {"venv", "env", "node_modules", "build", "dist", "__pycache__"}

def extract_git_velocity(repo_path: str, days: int = 30) -> Dict[str, int]:
    """Compute commit frequency per file over the last `days`."""
    repo_path_obj = Path(repo_path)
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    file_commit_counts: Dict[str, int] = {}

    # Target supported extensions for velocity
    extensions = {".py", ".sql", ".yml", ".yaml", ".js", ".ts"}

    files = [f for f in repo_path_obj.rglob("*")
             if f.is_file() and f.suffix.lower() in extensions]

    for file_path in files:
        if any(part in EXCLUDED_DIRS for part in file_path.parts):
            continue
        try:
            result = subprocess.run(
                ["git", "log", "--since", since_date, "--pretty=format:%H", str(file_path)],
                cwd=str(repo_path_obj),
                capture_output=True,
                text=True,
                check=True
            )
            count = len(result.stdout.splitlines())
            if count > 0:
                file_commit_counts[str(file_path)] = count
        except subprocess.CalledProcessError:
            continue
    return file_commit_counts

class Surveyor:
    """Static structure analyzer using multi-lingual Tree-sitter AST."""

    def __init__(self, kg: KnowledgeGraph, ts_analyzer: TreeSitterAnalyzer):
        self.kg = kg
        self.ts_analyzer = ts_analyzer

    def analyze_module(self, file_path: str) -> ModuleNode:
        ext = Path(file_path).suffix.lower()
        tree = self.ts_analyzer.get_tree(file_path)

        # Read file once for byte-offset decoding
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
            code_bytes = source_code.encode("utf-8")

        imports: List[str] = []
        public_functions: List[str] = []
        classes: List[str] = []

        if not tree:
            # Fallback registration for files without parsers
            self.kg.add_module(file_path)
        elif ext == ".py":
            self._analyze_python(tree, file_path, code_bytes, imports, public_functions, classes)
        elif ext == ".sql":
            self._analyze_sql(tree, file_path, source_code, imports)
        elif ext in {".yml", ".yaml"}:
            self._analyze_yaml(source_code, file_path, imports)

        # Register the module with extracted metadata
        self.kg.add_module(file_path, attrs={
            "public_functions": public_functions,
            "classes": classes,
            "imports": imports,
        })

        return ModuleNode(
            path=file_path,
            language=ext.replace(".", ""),
            is_dead_code_candidate=False,
            purpose_statement=None,    # Explicitly pass None
            domain_cluster=None,
            complexity_score=None,
            change_velocity_30d=None,
            last_modified=None
        )

    def _analyze_python(self, tree, file_path, code_bytes, imports, funcs, classes):
        """Python-specific AST traversal."""
        root = tree.root_node
        for node in root.children:
            # Extract Imports
            if node.type in {"import_statement", "import_from_statement"}:
                # Simplified: finding all dotted names within an import
                # A more robust version would walk the sub-tree
                for child in node.children:
                    if child.type == "dotted_name" or child.type == "aliased_import":
                        name = code_bytes[child.start_byte:child.end_byte].decode("utf-8")
                        imports.append(name)
                        self.kg.add_import(file_path, name)

            # Extract Functions
            elif node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = code_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8")
                    if not name.startswith("_"):
                        funcs.append(name)

    def _analyze_sql(self, tree, file_path, source_code, imports):
        """
        Extract table references and dbt 'ref' calls.
        Note: Standard Tree-sitter-sql might choke on Jinja,
        so we combine AST with Regex for dbt.
        """
        # 1. Regex for dbt references (Jaffle Shop critical!)
        dbt_refs = re.findall(r"\{\{\s*ref\(['\"](\w+)['\"]\)\s*\}\}", source_code)
        for ref in dbt_refs:
            imports.append(ref)
            self.kg.add_import(file_path, ref)

        # 2. AST check for standard SQL JOINs/FROMs
        # We look for identifiers within table_reference nodes
        def walk_sql(node):
            if node.type == "table_reference" or node.type == "relation":
                name = source_code[node.start_byte:node.end_byte]
                if name.lower() not in {"select", "from", "join", "where"}:
                    imports.append(name)
                    self.kg.add_import(file_path, name)
            for child in node.children:
                walk_sql(child)

        walk_sql(tree.root_node)

    def _analyze_yaml(self, source_code, file_path, imports):
        """Extract dbt sources or config dependencies from YAML."""
        # Simple regex for dbt source patterns in YAML
        sources = re.findall(r"source\s*:\s*(\w+)", source_code)
        for s in sources:
            imports.append(s)
            self.kg.add_import(file_path, s)

    def analyze_repo(self, repo_path: str):
        repo_path_obj = Path(repo_path)
        # Find all files supported by the analyzer
        supported_files = [
            f for f in repo_path_obj.rglob("*")
            if f.is_file() and f.suffix.lower() in {".py", ".sql", ".yml", ".yaml", ".js", ".ts"}
        ]

        velocity_map = extract_git_velocity(repo_path)

        for file_path in supported_files:
            if any(part in EXCLUDED_DIRS for part in file_path.parts):
                continue

            str_path = str(file_path)
            self.analyze_module(str_path)

            # Attach velocity if present
            if str_path in velocity_map:
                if str_path in self.kg.module_graph:
                    self.kg.module_graph.nodes[str_path]["change_velocity_30d"] = velocity_map[str_path]

        return self.kg
