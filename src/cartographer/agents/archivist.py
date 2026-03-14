# src/cartographer/agents/archivist.py
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from networkx import pagerank
from src.cartographer.agents.surveyor import Surveyor
from src.cartographer.graph.knowledge_graph import KnowledgeGraph
from src.cartographer.agents.semanticist import Semanticist

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

# ----------------------------------------------------
# Archivist: Living Context Maintainer
# ----------------------------------------------------

class Archivist:
    """
    Maintains living context artifacts for FDE onboarding and downstream tooling.

    Responsibilities:
    - CODEBASE.md: comprehensive living context
    - onboarding_brief.md: Day-One answers
    - lineage_graph.json: serialized data lineage
    - semantic_index/: vector store of Purpose Statements
    - cartography_trace.jsonl: audit log of agent actions
    """

    def __init__(self, kg: KnowledgeGraph, surveyor: Surveyor, semanticist: Semanticist, artifacts_dir: str = ".cartography"):
        self.kg = kg
        self.surveyor = surveyor
        self.semanticist = semanticist
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(exist_ok=True)
        self.semantic_index_dir = self.artifacts_dir / "semantic_index"
        self.semantic_index_dir.mkdir(exist_ok=True)
        self.trace_file = self.artifacts_dir / "cartography_trace.jsonl"

        # Initialize or load incremental vector store
        self.purpose_vectors: Dict[str, List[float]] = {}

    # ----------------------------------------------------
    # CODEBASE.md generation
    # ----------------------------------------------------
    def generate_CODEBASE_md(self, top_k_modules: int = 5):
        """
        Generate living CODEBASE.md with all requested sections:
        Architecture Overview, Critical Path, Data Sources & Sinks,
        Known Debt, High-Velocity Files, Module Purpose Index
        """
        md_path = self.artifacts_dir / "CODEBASE.md"

        # Architecture Overview (1 paragraph)
        arch_overview = "This codebase implements a modular data platform. Modules are organized around ingestion, " \
        "transformation, and output layers. Critical data pipelines and high-change areas are documented for FDE onboarding."

        # Critical Path (PageRank top-k modules)
        pr_scores = pagerank(self.kg.module_graph)
        top_modules = sorted(pr_scores.items(), key=lambda x: x[1], reverse=True)[:top_k_modules]
        critical_path = "\n".join([f"- {mod} (score={score:.4f})" for mod, score in top_modules])

        # Data Sources & Sinks (from Hydrologist lineage graph)
        sources = [n for n, d in self.kg.lineage_graph.in_degree() if d == 0]
        sinks = [n for n, d in self.kg.lineage_graph.out_degree() if d == 0]
        data_section = f"Sources:\n- " + "\n- ".join(sources) + "\nSinks:\n- " + "\n- ".join(sinks)

        # Known Debt (circular deps + doc drift)
        circular_deps = [n for n, _ in self.surveyor.detect_cycles()]
        doc_drift = [mod for mod, drift in self.semanticist.doc_drift.items() if drift]
        known_debt = "\n".join([f"- {mod} (circular)" for mod in circular_deps] +
                               [f"- {mod} (doc drift)" for mod in doc_drift])

        # High-Velocity Files
        velocity = {mod: self.kg.module_graph.nodes[mod].get("git_velocity", 0) for mod in self.kg.module_graph.nodes}
        high_velocity = sorted(velocity.items(), key=lambda x: x[1], reverse=True)[:top_k_modules]
        high_velocity_md = "\n".join([f"- {mod} ({vel} changes)" for mod, vel in high_velocity])

        # Module Purpose Index
        purpose_index = "\n".join([f"- {mod}: {purpose}" for mod, purpose in self.semanticist.purpose_statements.items()])

        # Assemble markdown
        md_content = f"""
# CODEBASE.md

## Architecture Overview
{arch_overview}

## Critical Path
{critical_path}

## Data Sources & Sinks
{data_section}

## Known Debt
{known_debt}

## High-Velocity Files
{high_velocity_md}

## Module Purpose Index
{purpose_index}
"""

        md_path.write_text(md_content.strip())
        self._log_trace("generate_CODEBASE_md", md_path, confidence=1.0)

        return md_path

    # ----------------------------------------------------
    # Onboarding brief
    # ----------------------------------------------------
    def generate_onboarding_brief(self):
        """
        Produce Day-One brief using Semanticist's answers.
        """
        answers = self.semanticist.answer_day_one_questions()
        brief_path = self.artifacts_dir / "onboarding_brief.md"

        brief_content = f"""
# Day-One FDE Brief

Generated on {datetime.now().isoformat()}

{answers}
"""
        brief_path.write_text(brief_content.strip())
        self._log_trace("generate_onboarding_brief", brief_path, confidence=0.95)

        return brief_path

    # ----------------------------------------------------
    # Serialize lineage graph
    # ----------------------------------------------------
    def serialize_lineage_graph(self):
        path = self.artifacts_dir / "lineage_graph.json"
        self.kg.serialize_lineage_graph(str(path))
        self._log_trace("serialize_lineage_graph", path, confidence=1.0)
        return path

    # ----------------------------------------------------
    # Build semantic index (vector store)
    # ----------------------------------------------------
    def build_semantic_index(self):
        """
        Stores each module's purpose embedding for semantic search.
        """
        for module, purpose in self.semanticist.purpose_statements.items():
            embedding = self.semanticist._embed_text(purpose)
            self.purpose_vectors[module] = embedding
            out_file = self.semantic_index_dir / f"{module.replace('/', '_')}.pkl"
            with open(out_file, "wb") as f:
                pickle.dump(embedding, f)
            self._log_trace("build_semantic_index", out_file, confidence=0.95)

        return self.semantic_index_dir

    # ----------------------------------------------------
    # Trace logging
    # ----------------------------------------------------

    def _log_trace(
            self,
            action: str,
            artifact_path: Path,
            confidence: float = 1.0,
            extra: Optional[dict[str, Any]] = None
        ):
        extra = extra or {}

        trace_entry = {
            "action": action,
            "artifact": str(artifact_path),
            "confidence": confidence,
            "extra": extra
        }

        with open(self.trace_file, "a") as f:
            f.write(json.dumps(trace_entry) + "\n")


    # ----------------------------------------------------
    # Incremental update support
    # ----------------------------------------------------
    def incremental_update(self, changed_files: List[str]):
        """
        Re-analyze only the changed files
        """
        # Update Semanticist purpose statements for changed files
        for file_path in changed_files:
            self.semanticist.generate_purpose_statement(file_path)

        # Rebuild CODEBASE.md and semantic index
        self.generate_CODEBASE_md()
        self.build_semantic_index()
        self.generate_onboarding_brief()
