# src/cartographer/agents/archivist.py

import json
import pickle
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.cartographer.agents.surveyor import Surveyor
from src.cartographer.agents.hydrologist import Hydrologist
from src.cartographer.agents.semanticist import Semanticist
from src.cartographer.graph.knowledge_graph import KnowledgeGraph


class Archivist:
    """
    Maintains living context artifacts for FDE onboarding and downstream tooling.

    Responsibilities:
    - CODEBASE.md
    - onboarding_brief.md
    - lineage_graph.json
    - semantic_index/
    - cartography_trace.jsonl
    """

    def __init__(
        self,
        kg: KnowledgeGraph,
        surveyor: Surveyor,
        hydrologist: Hydrologist,
        semanticist: Semanticist,
        artifacts_dir: Path | str = ".cartography",
    ):
        self.kg = kg
        self.surveyor = surveyor
        self.hydrologist = hydrologist
        self.semanticist = semanticist

        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(exist_ok=True)

        self.semantic_index_dir = self.artifacts_dir / "semantic_index"
        self.semantic_index_dir.mkdir(exist_ok=True)

        self.trace_file = self.artifacts_dir / "cartography_trace.jsonl"

        self.purpose_vectors: Dict[str, List[float]] = {}

    # ----------------------------------------------------
    # CODEBASE.md generation
    # ----------------------------------------------------

    def generate_CODEBASE_md(self, top_k_modules: int = 5):
        """Generate living CODEBASE.md."""

        md_path = self.artifacts_dir / "CODEBASE.md"

        arch_overview = (
            "This codebase implements a modular data platform. "
            "Modules are organized around ingestion, transformation, "
            "and output layers. Critical data pipelines and high-change "
            "areas are documented for FDE onboarding."
        )

        # Critical Path
        top_modules = self.surveyor.find_architectural_hubs(top_k_modules)
        critical_path = "\n".join(
            f"- {mod} (score={score:.4f})" for mod, score in top_modules
        )

        # Data Sources & Sinks
        sources = self.hydrologist.find_sources()
        sinks = self.hydrologist.find_sinks()

        data_section = (
            "Sources:\n- " + "\n- ".join(sources) +
            "\nSinks:\n- " + "\n- ".join(sinks)
        )

        # Known Debt
        cycles = self.surveyor.detect_cycles()
        circular_deps = [" -> ".join(cycle) for cycle in cycles]

        doc_drift = [
            mod for mod, drift in self.semanticist.doc_drift.items()
            if drift
        ]

        known_debt = "\n".join(
            [f"- {c} (circular)" for c in circular_deps] +
            [f"- {mod} (doc drift)" for mod in doc_drift]
        )

        # High Velocity Files
        velocity = {
            mod: self.kg.module_graph.nodes[mod].get("change_velocity_30d", 0)
            for mod in self.kg.module_graph.nodes
        }

        high_velocity = [
            (mod, vel) for mod, vel in velocity.items() if vel > 0
        ]

        high_velocity = sorted(
            high_velocity,
            key=lambda x: x[1],
            reverse=True
        )[:top_k_modules]

        high_velocity_md = "\n".join(
            f"- {mod} ({vel} changes)" for mod, vel in high_velocity
        )

        # Module Purpose Index
        purpose_index = "\n".join(
            f"- {mod}: {purpose}"
            for mod, purpose in self.semanticist.purpose_statements.items()
        )

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

        self._log_trace(
            "generate_CODEBASE_md",
            md_path,
            confidence=1.0
        )

        return md_path

    # ----------------------------------------------------
    # Onboarding Brief
    # ----------------------------------------------------

    def generate_onboarding_brief(self):
        """Produce Day-One FDE brief."""

        answers = self.semanticist.answer_day_one_questions()

        brief_path = self.artifacts_dir / "onboarding_brief.md"

        brief_content = f"""
# Day-One FDE Brief

Generated on {datetime.now().isoformat()}

{answers}
"""

        brief_path.write_text(brief_content.strip())

        self._log_trace(
            "generate_onboarding_brief",
            brief_path,
            confidence=0.95
        )

        return brief_path

    # ----------------------------------------------------
    # Serialize lineage graph
    # ----------------------------------------------------

    def serialize_lineage_graph(self):
        path = self.artifacts_dir / "lineage_graph.json"

        self.kg.serialize_lineage_graph(str(path))

        self._log_trace(
            "serialize_lineage_graph",
            path,
            confidence=1.0
        )

        return path

    # ----------------------------------------------------
    # Semantic Index
    # ----------------------------------------------------

    def build_semantic_index(self):
        """Store module purpose embeddings."""

        for module, purpose in self.semanticist.purpose_statements.items():
            embedding = self.semanticist._embed_text(purpose)

            self.purpose_vectors[module] = embedding

            out_file = self.semantic_index_dir / f"{module.replace('/', '_')}.pkl"

            with open(out_file, "wb") as f:
                pickle.dump(embedding, f)

            self._log_trace(
                "build_semantic_index",
                out_file,
                confidence=0.95
            )

        return self.semantic_index_dir

    # ----------------------------------------------------
    # Trace logging
    # ----------------------------------------------------

    def _log_trace(
        self,
        action: str,
        artifact_path: Path,
        confidence: float = 1.0,
        extra: Optional[dict[str, Any]] = None,
    ):
        extra = extra or {}

        trace_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "artifact": str(artifact_path),
            "confidence": confidence,
            "evidence_source": extra.get("evidence_source", "static_analysis"),
            "extra": extra,
        }

        with open(self.trace_file, "a") as f:
            f.write(json.dumps(trace_entry) + "\n")

    # ----------------------------------------------------
    # Incremental Update
    # ----------------------------------------------------

    def incremental_update(self, changed_files: List[str]):
        """Re-analyze only changed files."""

        for file_path in changed_files:
            self.semanticist.generate_purpose_statement(file_path)

        self.generate_CODEBASE_md()
        self.build_semantic_index()
        self.generate_onboarding_brief()
