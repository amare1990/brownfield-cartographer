# src/cartographer/agents/navigator.py

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import Any, List, Optional, Dict

from src.cartographer.graph.knowledge_graph import KnowledgeGraph
from src.cartographer.agents.semanticist import Semanticist
from src.cartographer.agents.hydrologist import Hydrologist
from src.cartographer.agents.archivist import Archivist


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
    def find_implementation(self, concept: str, top_k: int = 5, similarity_threshold: float = 0.7) -> List[Dict]:
        matches: List[Dict] = []

        concept_vector = np.array(self.semanticist._embed_text(concept)).reshape(1, -1)

        for module, emb in self.archivist.purpose_vectors.items():
            emb_vector = np.array(emb).reshape(1, -1)
            sim = cosine_similarity(concept_vector, emb_vector)[0][0]
            if sim >= similarity_threshold:
                matches.append({
                    "module": module,
                    "similarity": sim,
                    "evidence_source": "LLM",
                    "lines": (None, None)
                })

        matches.sort(key=lambda x: x["similarity"], reverse=True)
        return matches[:top_k]

    # ----------------------------------------------------
    # Tool 2: Trace Lineage
    # ----------------------------------------------------
    def trace_lineage(self, dataset: str, direction: str = "upstream") -> List[Dict]:
        results: List[Dict] = []

        if dataset not in self.kg.lineage_graph.nodes:
            return [{"error": f"Dataset '{dataset}' not found in lineage graph."}]

        nodes = (self.kg.lineage_graph.predecessors(dataset) if direction == "upstream"
                 else self.kg.lineage_graph.successors(dataset))

        for n in nodes:
            edge_data = self.kg.lineage_graph.get_edge_data(n, dataset)
            metadata = edge_data.get("metadata", {}) if edge_data else {}
            results.append({
                "module": n,
                "source": metadata.get("evidence_source", "static_analysis"),
                "lines": (metadata.get("line_start"), metadata.get("line_end")),
                "file": metadata.get("file")
            })

        return results

    # ----------------------------------------------------
    # Tool 3: Blast Radius
    # ----------------------------------------------------
    def blast_radius(self, module_path: str) -> List[Dict]:
        if module_path not in self.kg.module_graph.nodes:
            return [{"error": f"Module '{module_path}' not found in module graph."}]
        affected = list(self.kg.module_graph.successors(module_path))
        return [{"module": m} for m in affected]

    # ----------------------------------------------------
    # Tool 4: Explain Module
    # ----------------------------------------------------
    def explain_module(self, path: str) -> Dict:
        purpose = self.semanticist.purpose_statements.get(path)
        if not purpose:
            return {"module": path, "error": "No purpose statement available."}

        doc_drift = self.semanticist.doc_drift.get(path, False)
        return {
            "module": path,
            "purpose": purpose,
            "doc_drift": doc_drift,
            "drift_msg": "⚠️ Documentation drift detected" if doc_drift else "Documentation matches purpose"
        }

    # ----------------------------------------------------
    # Generic Query Interface
    # ----------------------------------------------------
    def query(self, tool_name: str, *args, **kwargs) -> Any:
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
    def query_chain(self, steps: List[Dict]) -> Optional[Any]:
        result: Any = None
        for step in steps:
            tool = step["tool"]
            args = step.get("args", [])
            kwargs = step.get("kwargs", {})
            if result is not None and step.get("pass_prev", False):
                args = [result] + args
            result = self.query(tool, *args, **kwargs)
        return result
