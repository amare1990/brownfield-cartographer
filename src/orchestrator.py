# src/orchestrator.py
from pathlib import Path
from src.cartographer.graph.knowledge_graph import KnowledgeGraph
from src.cartographer.analyzers.tree_sitter_analyzer import TreeSitterAnalyzer
from src.cartographer.agents.surveyor import Surveyor
from src.cartographer.agents.hydrologist import Hydrologist
from tree_sitter import Parser, Language
import tree_sitter_python as tspython

# ---------- Setup KnowledgeGraph ----------
kg = KnowledgeGraph()

# ---------- Initialize Agents ----------
ts_analyzer = TreeSitterAnalyzer()
surveyor = Surveyor(kg, ts_analyzer)
hydrologist = Hydrologist(kg, ts_analyzer)

# ---------- Setup Python parser for Hydrologist ----------
PY_LANGUAGE = Language(tspython.language())
# python_parser = Parser()
python_parser = Parser(PY_LANGUAGE)

def run_repo_analysis(repo_path: str):
    repo_path_obj = Path(repo_path)

    # 1️⃣ Run Surveyor → module graph
    print("\n" + "*" * 40 + " Running Surveyor " + "*" * 60 + "\n")
    surveyor.analyze_repo(str(repo_path_obj))
    print(f"Module graph nodes: {len(kg.module_graph.nodes)}")
    print(f"Module graph edges: {len(kg.module_graph.edges)}")

    # ---- NEW: Graph analytics (reviewer request) ----
    print("\n" + "*" * 40 + " Graph Analytics " + "*" * 60 + "\n")
    hubs = surveyor.find_architectural_hubs()
    cycles = surveyor.detect_cycles()
    dead_code = surveyor.detect_dead_code()

    print(f"Top architectural hubs: {hubs[:5]}")
    print(f"Circular dependencies: {cycles}")
    print(f"Dead code candidates: {dead_code[:10]}")

    # 2️⃣ Run Hydrologist → lineage graph
    print("\n" + "*" * 40 + " Running Hydrologist " + "*" * 60 + "\n")
    print("Running Hydrologist (data lineage analysis)...")
    hydrologist.analyze_repo(str(repo_path_obj))
    print(f"Lineage graph nodes: {len(kg.lineage_graph.nodes)}")
    print(f"Lineage graph edges: {len(kg.lineage_graph.edges)}")

    # 3️⃣ Serialize graphs
    print("\n" + "*" * 40 + " Serializing Graphs " + "*" * 40 + "\n")
    CARTOGRAPHY_DIR = Path.cwd() / ".cartography"
    CARTOGRAPHY_DIR.mkdir(exist_ok=True)

    module_graph_path = CARTOGRAPHY_DIR / "module_graph.json"
    lineage_graph_path = CARTOGRAPHY_DIR / "lineage_graph.json"

    kg.serialize_module_graph(str(module_graph_path))
    kg.serialize_lineage_graph(str(lineage_graph_path))

    print(f"Module graph saved to {module_graph_path}")
    print(f"Lineage graph saved to {lineage_graph_path}")

# Example usage:
# run_repo_analysis("data/sample_repos/jaffle_shop")
