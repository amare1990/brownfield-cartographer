
---
# Brownfield Cartographer

```markdown

**Cartographer** is a multi-agent repository intelligence system designed to analyze codebases, extract structural module information, and map data lineage. It combines static code analysis (Surveyor), dataflow analysis (Hydrologist), and configuration parsing (DAG/DBT) into a centralized **Knowledge Graph**.
```
---


**Author: Amare Kassa**

**email: amaremek@gmail.com**

---

## 🧩 Project Overview

Cartographer helps you:


  * Build a **module dependency graph** (imports, functions, classes) via **Surveyor**

  * Build a **data lineage graph** from SQL, Python, and DAG configurations via **Hydrologist**

  * Track file **change velocity** via Git history

  * Generate **semantic insights** for modules using **Semanticist** (purpose statements, doc drift, domain clustering)

  * Maintain **living artifacts** with **Archivist** (CODEBASE.md, onboarding briefs, semantic embeddings)

  * Explore the codebase interactively using **Navigator** (semantic queries, blast radius, lineage tracing)

  * Produce structured JSON outputs and textual artifacts for downstream analysis or FDE onboarding

  * Support multi-phase development (Phase0 → Phase4) for iterative, agentic repo intelligence

---

## 📁 Repository Structure

```

# Brownfield Cartographer

**Brownfield Cartographer** is a multi-agent codebase intelligence system that analyzes repositories for module structure, data lineage, and overall onboarding insights. It integrates **Surveyor** (module structure), **Hydrologist** (data lineage), and various analyzers for Python, SQL, and DAG/YAML.

---

## Repo Structure
brownfield-cartographer/
├─ data/                        # Sample repositories and outputs
│  └─ <repo_name>/
│     └─ .cartography/          # Generated artifacts per repo
│        ├─ module_graph.json
│        ├─ lineage_graph.json
│        ├─ CODEBASE.md
│        ├─ onboarding_brief.md
│        └─ semantic_index/     # Module embeddings for Navigator queries
├─ src/
│  ├─ cartographer/
│  │  ├─ agents/
│  │  │  ├─ surveyor.py         # Static module structure analysis
│  │  │  ├─ hydrologist.py      # Data lineage analysis
│  │  │  ├─ semanticist.py      # LLM-powered semantic insights
│  │  │  ├─ archivist.py        # Artifact management & semantic index
│  │  │  └─ navigator.py        # Interactive querying over KnowledgeGraph
│  │  ├─ analyzers/             # File analyzers
│  │  │  ├─ sql_lineage.py
│  │  │  ├─ dag_config_parser.py
│  │  │  └─ tree_sitter_analyzer.py
│  │  ├─ graph/
│  │  │  └─ knowledge_graph.py  # Central KnowledgeGraph (modules & lineage)
│  │  └─ models/
│  │     └─ node.py             # ModuleNode, FunctionNode, DatasetNode
         └─ lineage.py             # LineageEdge
│  ├─ cli.py                    # CLI entrypoint
│  └─ orchestrator.py           # Orchestration of all agents & interactive Navigator
├─ tests/                        # Unit & integration tests
├─ pyproject.toml                # Project dependencies and config
└─ README.md                     # Project overview, setup, and instructions

````

---

## ⚙️ Installation

```bash
# Clone the repository
git clone https://github.com/amare1990/brownfield-cartographer.git
cd brownfield-cartographer

# Set up Python environment
python -m venv venv
source venv/bin/activate

# Install dependencies
uv sync
````

---

## 🚀 Usage

### Analyze a Repository

```bash
# Run the CLI to analyze a repo (example: jaffle_shop)
uv run python -m src.cli data/jaffle_shop
```

**Outputs:**

* Module graph JSON: `.cartography/module_graph.json`
* Lineage graph JSON: `.cartography/lineage_graph.json`
* CODEBASE.md: `.cartography/CODEBASE.md`
* Day-One FDE brief: `.cartography/onboarding_brief.md`
* Semantic embeddings: `.cartography/semantic_index/`

## Test
```bash
uv run python -m pytest
```

### Key Features

* **Surveyor**: Extracts Python module structure, classes, public functions, and imports.
* **Hydrologist**: Extracts data lineage from Python, SQL, and DAG/YAML configurations.
* **Git Velocity**: Annotates modules/datasets with commit frequency over the last N days.
* **Tree-sitter Parsers**: Support for Python, SQL, YAML, JS/TS modules.
* **Semanticist**: Generates purpose statements for each module using LLMs, detects documentation drift, clusters modules into domains, and produces onboarding answers for FDEs.

* **Archivist**: Maintains living artifacts for FDE onboarding, including CODEBASE.md, onboarding briefs, lineage snapshots, and semantic embeddings for downstream querying.

* **Navigator**: Provides interactive, LLM-assisted query tools over the codebase knowledge graph:

    * `find_implementation(concept)` – find modules semantically implementing a concept

    * `trace_lineage(dataset, direction)` – trace upstream/downstream data flow

    * `blast_radius(module)` – modules impacted by changes

    * `explain_module(module)` – summarize module purpose and doc drift

---

## 🛠 Development

* **Branching Convention:** `feat/<feature>` for new features, `fix/<bug>` for fixes.
* **Testing:** Place unit tests in `tests/`, run using `pytest`.
* **Code Quality:** Follow PEP-8; use `black` for formatting and `mypy` for type checking.

---

## 📊 Knowledge Graph

The **KnowledgeGraph** is central to Cartographer:

* **Module Graph**: Nodes = modules, edges = imports/dependencies
* **Lineage Graph**: Nodes = datasets, edges = data flow dependencies
* **Queries Supported**:

  * `blast_radius(node)` – downstream nodes affected by a change
  * `find_sources()` – nodes with no incoming edges
  * `find_sinks()` – nodes with no outgoing edges
* Supports serialization to JSON for analysis or visualization.

---

## 🧪 Common Workflows

1. **Add a new repository to analyze**
2. **Run CLI** → JSON artifacts generated in `.cartography/`
3. **Inspect graphs** and domain clusters using NetworkX or visualization libraries
4. **Iterate with new analyzers** to query concepts, trace datasets, or understand module impact
5. **Iterate with updated Semanticist/Archivist runs** to refresh embeddings and insights

---

## 📌 Notes

* Ensure that Python files exist in the target repo to populate the **module graph**; otherwise, Surveyor will create dummy nodes.
* Hydrologist requires **SQL or DAG/YAML files** to populate the lineage graph.
* Tree-sitter parser libraries must be installed for each language (`tree_sitter_python`, `tree_sitter_sql`, etc.)

---

## 🔗 References

* [Tree-sitter](https://tree-sitter.github.io/tree-sitter/)
* [NetworkX](https://networkx.org/)
* [sqlglot](https://github.com/tobymao/sqlglot)
* [DBT](https://www.getdbt.com/)
* [Airflow](https://airflow.apache.org/)

---
