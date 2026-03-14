# src/cartographer/agents/navigator.py

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from typing import Any, List, Optional

from src.cartographer.graph.knowledge_graph import KnowledgeGraph
from src.cartographer.agents.semanticist import Semanticist
from src.cartographer.agents.hydrologist import Hydrologist
from src.cartographer.agents.archivist import Archivist

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

    def __init__(self, kg: KnowledgeGraph, semanticist: Semanticist, hydrologist: Hydrologist, archivist: Archivist):
        self.kg = kg
        self.semanticist = semanticist
        self.hydrologist = hydrologist
        self.archivist = archivist

    # ----------------------------------------------------
    # Tool 1: Find Implementation
    # ----------------------------------------------------

    def find_implementation(
            self,
            concept: str,
            top_k: int = 5,
            similarity_threshold: float = 0.7
        ) -> list[str]:
        """
        Find modules implementing a concept using semantic similarity.

        Args:
            concept: The concept to search for.
            top_k: Maximum number of modules to return.
            similarity_threshold: Minimum cosine similarity to include a module.

        Returns:
            List of module paths most semantically related to the concept.
        """
        matches = []

        # Step 1: Embed the concept
        concept_vector = np.array(self.semanticist._embed_text(concept)).reshape(1, -1)

        # Step 2: Compare against all module embeddings stored in Archivist
        for module, emb in self.archivist.purpose_vectors.items():
            emb_vector = np.array(emb).reshape(1, -1)  # convert list to 2D array
            sim = cosine_similarity(concept_vector, emb_vector)[0][0]
            if sim >= similarity_threshold:
                matches.append((module, sim))

        # Step 3: Sort by similarity descending
        matches.sort(key=lambda x: x[1], reverse=True)

        # Step 4: Return top-k module paths
        return [module for module, _ in matches[:top_k]]

    # ----------------------------------------------------
    # Tool 2: Trace Lineage
    # ----------------------------------------------------
    def trace_lineage(self, dataset: str, direction: str = "upstream") -> List[dict]:
        results = []
        if dataset in self.kg.lineage_graph.nodes:
            nodes = self.kg.lineage_graph.predecessors(dataset) if direction == "upstream" else self.kg.lineage_graph.successors(dataset)
            for n in nodes:
                edge_data = self.kg.lineage_graph.get_edge_data(n, dataset)
                results.append({
                    "module": n,
                    "source": "static_analysis",
                    "lines": (edge_data.get("line_start"), edge_data.get("line_end")) if edge_data else (None, None)
                })
        return results


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

    # ----------------------------------------------------
    # Tool Chaining Interface
    # ----------------------------------------------------

    def query_chain(self, steps: list[dict]) -> Optional[Any]:
        """
        Execute a chain of tool calls.
        steps: [{"tool": "trace_lineage", "args": [...], "kwargs": {...}}, ...]
        Returns the final result of the last tool.
        """
        result: Any = None
        for step in steps:
            tool = step["tool"]
            args = step.get("args", [])
            kwargs = step.get("kwargs", {})
            if result is not None and step.get("pass_prev", False):
                args = [result] + args
            result = self.query(tool, *args, **kwargs)
        return result


