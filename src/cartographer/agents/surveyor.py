from pathlib import Path

from cartographer.graph.module_graph import ModuleGraph
from cartographer.analyzers.tree_sitter_analyzer import TreeSitterAnalyzer


class Surveyor:

    def __init__(self):
        self.analyzer = TreeSitterAnalyzer()

    def analyze_repo(self, repo_path: Path):

        graph = ModuleGraph()

        for path in repo_path.rglob("*.py"):

            module = str(path)
            graph.add_module(module)

            imports = self.analyzer.extract_imports(path)

            for imp in imports:
                graph.add_import(module, imp)

        return graph
