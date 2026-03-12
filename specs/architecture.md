# Brownfield Cartographer - Architecture

## Overview
The Cartographer is a multi-agent system with a central knowledge graph and a query interface.

### Components
- **Surveyor** → builds structural skeleton of modules and imports
- **Hydrologist** → constructs DataLineageGraph across Python/SQL/YAML
- **Semanticist** → generates module purpose statements and domain clustering
- **Archivist** → maintains living context and produces CODEBASE.md and onboarding briefs
- **Navigator** → LangGraph agent to query the knowledge graph

### Data Flow
1. repo_inventory → analyzers → agents → knowledge graph
2. Outputs stored in `.cartography/`
   - module_graph.json
   - lineage_graph.json
   - onboarding_brief.md
   - CODEBASE.md
   - cartography_trace.jsonl

### Storage
- Knowledge Graph: NetworkX (structure + lineage)
- Vector store: semantic search for module purpose statements
