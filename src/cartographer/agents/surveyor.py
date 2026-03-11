# Surveyor agent for static structure analysis of codebases.
# This agent uses the KnowledgeGraph to analyze module imports and compute architectural insights like PageRank and strongly connected components.
# src/cartographer/agents/surveyor.py

import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict

from src.cartographer.graph.knowledge_graph import KnowledgeGraph
import networkx as nx


def extract_git_velocity(repo_path: str, days: int = 30) -> Dict[str, int]:
    """
    Compute commit frequency per file over the last `days` in the Git repository.

    Args:
        repo_path: Path to the repo root (string)
        days: Number of days to look back in git history

    Returns:
        Dictionary mapping file paths to number of commits
    """
    # Convert string to Path internally
    repo_path_obj = Path(repo_path)
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    file_commit_counts: Dict[str, int] = {}

    # rglob only works on Path objects
    files = [f for f in repo_path_obj.rglob("*") if f.is_file()]

    for file_path in files:
        try:
            # subprocess.run requires string paths
            result = subprocess.run(
                ["git", "log", "--since", since_date, "--follow", "--pretty=format:%H", str(file_path)],
                cwd=str(repo_path_obj),
                capture_output=True,
                text=True,
                check=True
            )
            commit_count = len(result.stdout.splitlines())
            file_commit_counts[str(file_path)] = commit_count
        except subprocess.CalledProcessError:
            continue

    # Identify top 20% high-velocity files
    if file_commit_counts:
        sorted_files = sorted(file_commit_counts.items(), key=lambda x: x[1], reverse=True)
        top_20pct_index = max(1, len(sorted_files) * 20 // 100)
        high_velocity_files = {f: c for f, c in sorted_files[:top_20pct_index]}
        for f, c in sorted_files[top_20pct_index:]:
            high_velocity_files[f] = c

        return high_velocity_files

    return {}

class Surveyor:
    """Static structure analyzer using module imports and AST."""

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg

    def analyze_module(self, module_name: str, imports: list[str]):
        """Add module and its imports to the graph."""
        self.kg.add_module(module_name)
        for imp in imports:
            self.kg.add_import(module_name, imp)

    def compute_pagerank(self):
        """Compute PageRank hubs for architectural insight."""
        pr = nx.pagerank(self.kg.module_graph)
        return pr

    def strongly_connected_components(self):
        """Return circular dependencies as sets of module names."""
        return list(nx.strongly_connected_components(self.kg.module_graph))
