import networkx as nx

class ModuleGraph:

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_module(self, module_path: str):
        self.graph.add_node(module_path)

    def add_import(self, source: str, target: str):
        self.graph.add_edge(source, target)

    def to_dict(self):
        return nx.node_link_data(self.graph)
