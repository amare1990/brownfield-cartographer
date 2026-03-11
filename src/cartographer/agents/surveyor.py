# Surveyor agent for static structure analysis of codebases.
# This agent uses the KnowledgeGraph to analyze module imports and compute architectural insights like PageRank and strongly connected components.
# src/cartographer/agents/surveyor.py

from src.cartographer.graph.knowledge_graph import KnowledgeGraph
import networkx as nx

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
