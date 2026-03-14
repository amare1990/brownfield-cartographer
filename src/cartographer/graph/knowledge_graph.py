# src/cartographer/graph/knowledge_graph.py
import networkx as nx
import json
from typing import Dict, List, Optional
from src.cartographer.models.node import DatasetNode
from src.cartographer.models.lineage import LineageEdge, EdgeType



VALID_STORAGE_TYPES = {"table", "file", "stream", "api"}

class KnowledgeGraph:
    def __init__(self):
        self.module_graph = nx.DiGraph()
        self.lineage_graph = nx.DiGraph()

    # --- Module Graph Methods ---
    def add_module(self, path: str, attrs: Optional[Dict] = None):
        self.module_graph.add_node(path, **(attrs or {}))

    def add_import(self, source_path: str, target_module: str):
        self.module_graph.add_edge(source_path, target_module, type="IMPORTS")

    # --- Lineage Graph Methods (The Missing Pieces) ---
    def add_dataset(self, name: str, storage_type: str = "table", **kwargs):
        """
        Fixes the 'storage_type' error by creating a DatasetNode
        and adding it to the graph.
        """
        node_data = DatasetNode(name=name, storage_type=storage_type, **kwargs)
        # Store as dict for NetworkX compatibility
        self.lineage_graph.add_node(name, **node_data.model_dump())

    def add_lineage_edge(
        self, source: str, target: str, edge_type: EdgeType, weight: int = 1, metadata: Optional[dict] = None
    ):
        """
        Adds a directed edge in the lineage graph using LineageEdge.
        Ensures robust typing, provenance metadata, and default weight.
        """
        if metadata is None:
            metadata = {}

        edge_data = LineageEdge(
            source=source,
            target=target,
            edge_type=edge_type,
            weight=weight,
            metadata=metadata
        )

        self.lineage_graph.add_edge(source, target, **edge_data.model_dump())

    # --- Serialization ---
    def serialize_module_graph(self, output_path: str):
        data = nx.node_link_data(self.module_graph)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

    def serialize_lineage_graph(self, output_path: str):
        data = nx.node_link_data(self.lineage_graph)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

    # --- Analytics ---
    def blast_radius(self, node: str) -> List[str]:
        if node in self.lineage_graph:
            return list(nx.descendants(self.lineage_graph, node))
        return []

    def find_sources(self) -> List[str]:
        return [n for n, d in self.lineage_graph.in_degree() if d == 0]

    def find_sinks(self) -> List[str]:
        return [n for n, d in self.lineage_graph.out_degree() if d == 0]

    # --- Deserialization ---
    def load_module_graph(self, input_path: str):
        with open(input_path) as f:
            data = json.load(f)
        self.module_graph = nx.node_link_graph(data)

    def load_lineage_graph(self, input_path: str):
        with open(input_path) as f:
            data = json.load(f)
        self.lineage_graph = nx.node_link_graph(data)
