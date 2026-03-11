# Knowledge Graph for Cartographer
# This module defines the KnowledgeGraph class, which serves as a central graph for both structural modules and data lineage within the Cartographer system. It uses NetworkX to manage directed graphs for modules and lineage, allowing for easy addition of nodes and edges, as well as serialization to JSON format.

# src/cartographer/graph/knowledge_graph.py


import networkx as nx
import json
from typing import Dict, Any, Optional

class KnowledgeGraph:
    """Central graph for structural modules and data lineage."""

    def __init__(self):
        self.module_graph = nx.DiGraph()
        self.lineage_graph = nx.DiGraph()

    # ----- Module Graph -----
    def add_module(self, module_name: str, attrs: Optional[Dict[str, Any]] = None):
        self.module_graph.add_node(module_name, **(attrs or {}))

    def add_import(self, source: str, target: str):
        self.module_graph.add_edge(source, target)

    def serialize_module_graph(self, path: str):
        data = nx.node_link_data(self.module_graph)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    # ----- Lineage Graph -----
    def add_dataset(self, dataset_name: str, attrs: Optional[Dict[str, Any]] = None):
        self.lineage_graph.add_node(dataset_name, **(attrs or {}))

    def add_lineage(self, source: str, target: str, attrs: Optional[Dict[str, Any]] = None):
        self.lineage_graph.add_edge(source, target, **(attrs or {}))

    def serialize_lineage_graph(self, path: str):
        data = nx.node_link_data(self.lineage_graph)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    # ----- Graph queries -----
    def blast_radius(self, node: str):
        """Return all downstream nodes affected by a change to `node`."""
        return list(nx.descendants(self.lineage_graph, node))

    def find_sources(self):
        """Nodes with no incoming edges"""
        return [n for n, d in self.lineage_graph.in_degree() if d == 0]

    def find_sinks(self):
        """Nodes with no outgoing edges"""
        return [n for n, d in self.lineage_graph.out_degree() if d == 0]
