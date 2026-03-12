# Agent Roles Specification

## Surveyor
- Performs static code analysis
- Builds module graph
- Detects dead code, circular dependencies, and high-velocity files

## Hydrologist
- Builds DataLineageGraph
- Supports Python, SQL/dbt, YAML configs, Jupyter notebooks
- Can answer upstream/downstream and blast_radius queries

## Semanticist
- Generates module purpose statements via LLMs
- Detects documentation drift
- Clusters modules into business domains
- Synthesizes Five FDE Day-One answers

## Archivist
- Generates CODEBASE.md, onboarding_brief.md
- Maintains cartography_trace.jsonl
- Updates living context on new commits

## Navigator
- LangGraph agent with 4 tools: find_implementation, trace_lineage, blast_radius, explain_module
