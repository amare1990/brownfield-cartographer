# src/agents/navigator.py

from typing import Any, List

from src.cartographer.graph.knowledge_graph import KnowledgeGraph
from src.cartographer.agents.semanticist import Semanticist
from src.cartographer.agents.hydrologist import Hydrologist

# ----------------------------------------------------
# Navigator Agent
# ----------------------------------------------------

class Navigator:
    """
    LangGraph agent to query the codebase knowledge graph.
    Provides four tools:
      - find_implementation
      - trace_lineage
      - blast_radius
      - explain_module
    """

    def __init__(self, kg: KnowledgeGraph, semanticist: Semanticist, hydrologist: Hydrologist):
        self.kg = kg
        self.semanticist = semanticist
        self.hydrologist = hydrologist

    # ----------------------------------------------------
    # Tool 1: Find Implementation
    # ----------------------------------------------------
    def find_implementation(self, concept: str) -> List[str]:
        """
        Search module purpose statements for the concept.
        Returns matching module paths.
        """
        matches = []
        for module, purpose in self.semanticist.purpose_statements.items():
            if concept.lower() in purpose.lower():
                matches.append(module)
        return matches

    # ----------------------------------------------------
    # Tool 2: Trace Lineage
    # ----------------------------------------------------
    def trace_lineage(self, dataset: str, direction: str = "upstream") -> List[str]:
        """
        Trace data lineage for a dataset.
        direction: 'upstream' or 'downstream'
        Returns list of module paths producing/consuming the dataset.
        """
        lineage = []
        if dataset in self.kg.lineage_graph.nodes:
            if direction == "upstream":
                lineage = list(self.kg.lineage_graph.predecessors(dataset))
            else:
                lineage = list(self.kg.lineage_graph.successors(dataset))
        return lineage

    # ----------------------------------------------------
    # Tool 3: Blast Radius
    # ----------------------------------------------------
    def blast_radius(self, module_path: str) -> List[str]:
        """
        Returns downstream modules affected if module_path changes.
        """
        affected = []
        if module_path in self.kg.module_graph.nodes:
            affected = list(self.kg.module_graph.successors(module_path))
        return affected

    # ----------------------------------------------------
    # Tool 4: Explain Module
    # ----------------------------------------------------
    def explain_module(self, path: str) -> str:
        """
        Return the purpose statement and doc drift info for a module.
        """
        purpose = self.semanticist.purpose_statements.get(path, "No purpose statement available.")
        doc_drift = self.semanticist.doc_drift.get(path, False)
        drift_msg = "⚠️ Documentation drift detected" if doc_drift else "Documentation matches purpose"
        return f"{purpose}\n{drift_msg}"

    # ----------------------------------------------------
    # Generic Query Interface
    # ----------------------------------------------------
    def query(self, tool_name: str, *args, **kwargs) -> Any:
        """
        Dispatch to a tool by name.
        """
        tools = {
            "find_implementation": self.find_implementation,
            "trace_lineage": self.trace_lineage,
            "blast_radius": self.blast_radius,
            "explain_module": self.explain_module,
        }
        if tool_name not in tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        return tools[tool_name](*args, **kwargs)
