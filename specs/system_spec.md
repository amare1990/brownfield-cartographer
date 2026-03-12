# Brownfield Cartographer - System Specification

## Purpose
The system ingests any GitHub repository or local path and produces a living, queryable map of the system's architecture, data flows, and semantic structure.

## Scope
- Target: Data engineering & data science codebases (Python + SQL + YAML + Notebooks)
- Multi-agent architecture: Surveyor, Hydrologist, Semanticist, Archivist
- Outputs: CODEBASE.md, onboarding_brief.md, module_graph.json, lineage_graph.json, cartography_trace.jsonl

## High-Level Workflow
1. Repository scanning & inventory (RepoInventory)
2. Static analysis (Surveyor)
3. Data lineage extraction (Hydrologist)
4. Semantic analysis (Semanticist)
5. Living context & deliverables generation (Archivist)
6. Query interface (Navigator)
