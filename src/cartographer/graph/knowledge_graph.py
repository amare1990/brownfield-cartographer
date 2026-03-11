import networkx as nx
import json


class KnowledgeGraph:

    def __init__(self):
        self.module_graph = nx.DiGraph()
        self.lineage_graph = nx.DiGraph()

    def add_module(self, module):
        self.module_graph.add_node(module)

    def add_import(self, source, target):
        self.module_graph.add_edge(source, target)

    def add_dataset(self, dataset):
        self.lineage_graph.add_node(dataset)

    def add_lineage(self, source, target):
        self.lineage_graph.add_edge(source, target)

    def serialize_module_graph(self, path):

        data = nx.node_link_data(self.module_graph)

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def serialize_lineage_graph(self, path):

        data = nx.node_link_data(self.lineage_graph)

        with open(path, "w") as f:
            json.dump(data, f, indent=2)
