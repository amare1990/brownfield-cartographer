
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

- Build a **module dependency graph** (imports, functions, classes)
- Build a **data lineage graph** from SQL, Python, and DAG configurations
- Track **file change velocity** via Git history
- Produce structured JSON outputs for downstream analysis or visualization
- Support multi-phase development (Phase0 → Phase2) for iterative repo intelligence

---

## 📁 Repository Structure

```

# Brownfield Cartographer

**Brownfield Cartographer** is a multi-agent codebase intelligence system that analyzes repositories for module structure, data lineage, and overall onboarding insights. It integrates **Surveyor** (module structure), **Hydrologist** (data lineage), and various analyzers for Python, SQL, and DAG/YAML.

---

## Repo Structure

```text
brownfield-cartographer/
├─ data/                        # Sample repositories and outputs
│  └─ <repo_name>/
│     └─ .cartography/          # Generated module & lineage JSONs per repo
├─ src/
│  ├─ cartographer/
│  │  ├─ agents/                # Agent modules
│  │  │  ├─ surveyor.py         # Static module structure analysis
│  │  │  └─ hydrologist.py      # Data lineage analysis
│  │  ├─ analyzers/             # File analyzers
│  │  │  ├─ sql_lineage.py      # SQL dependency extraction
│  │  │  ├─ dag_config_parser.py# DAG/YAML parsing
│  │  │  └─ tree_sitter_analyzer.py # Tree-sitter AST traversal for multi-language
│  │  ├─ graph/                 # Graph models
│  │  │  └─ knowledge_graph.py  # Central KnowledgeGraph (modules & lineage)
│  │  └─ models/                # Data models
│  │     └─ node.py             # ModuleNode, FunctionNode, DatasetNode
│  ├─ cli.py                    # CLI entrypoint
│  └─ orchestrator.py           # Orchestration of Surveyor + Hydrologist
├─ tests/                        # Unit & integration tests
├─ pyproject.toml                # Project dependencies and config
└─ README.md                     # Project overview and instructions

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
uv run python -m src.cli data/sample_repos/jaffle_shop
```

**Outputs:**

* Module graph JSON: `.cartography/module_graph.json`
* Lineage graph JSON: `.cartography/lineage_graph.json`

### Key Features

* **Surveyor**: Extracts Python module structure, classes, public functions, and imports.
* **Hydrologist**: Extracts data lineage from Python, SQL, and DAG/YAML configurations.
* **Git Velocity**: Annotates modules/datasets with commit frequency over the last N days.
* **Tree-sitter Parsers**: Support for Python, SQL, YAML, JS/TS modules.

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
3. **Inspect graphs** using tools like [NetworkX](https://networkx.org/) or visualization libraries
4. **Iterate with new analyzers** for additional languages or custom rules

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
