# src/orchestrator.py
import tempfile
import subprocess
from subprocess import check_output
from pathlib import Path
from src.cartographer.graph.knowledge_graph import KnowledgeGraph
from src.cartographer.analyzers.tree_sitter_analyzer import TreeSitterAnalyzer
from src.cartographer.agents.surveyor import Surveyor
from src.cartographer.agents.hydrologist import Hydrologist
from src.cartographer.agents.semanticist import Semanticist
from src.cartographer.agents.archivist import Archivist
from src.cartographer.agents.navigator import Navigator
from tree_sitter import Parser, Language
import tree_sitter_python as tspython


CARTOGRAPHY_DIR = Path.cwd() / ".cartography"
CARTOGRAPHY_DIR.mkdir(exist_ok=True)

# ---------- Setup KnowledgeGraph ----------
kg = KnowledgeGraph()

# ---------- Initialize Agents ----------
ts_analyzer = TreeSitterAnalyzer()
surveyor = Surveyor(kg, ts_analyzer)
hydrologist = Hydrologist(kg, ts_analyzer)
semanticist = Semanticist(kg)
archivist = Archivist(
    kg=kg,
    surveyor=surveyor,
    hydrologist=hydrologist,
    semanticist=semanticist,
    artifacts_dir=Path(CARTOGRAPHY_DIR)
)
archivist.build_semantic_index()  # ensure embeddings exist
navigator = Navigator(kg, semanticist, hydrologist, archivist)

# ---------- Setup Python parser for Hydrologist ----------
PY_LANGUAGE = Language(tspython.language())
# python_parser = Parser()
python_parser = Parser(PY_LANGUAGE)



def clone_repo_if_needed(repo_path: str) -> str:
    if repo_path.startswith("http"):
        tmp = tempfile.mkdtemp()
        subprocess.run(["git", "clone", repo_path, tmp])
        return tmp
    return repo_path


def run_repo_analysis(repo_path: str):
    repo_path = clone_repo_if_needed(repo_path)
    repo_path_obj = Path(repo_path)

    # 0️⃣ Detect changed files
    def get_changed_files(repo_path: str) -> list[str]:
        try:
            result = check_output(["git", "diff", "--name-only", "HEAD~1", "HEAD"], cwd=repo_path)
            return result.decode().splitlines()
        except Exception:
            return []

    changed_files = get_changed_files(str(repo_path_obj))
    is_first_run = not (CARTOGRAPHY_DIR / "CODEBASE.md").exists()

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
    # CARTOGRAPHY_DIR = Path.cwd() / ".cartography"
    # CARTOGRAPHY_DIR.mkdir(exist_ok=True)

    module_graph_path = CARTOGRAPHY_DIR / "module_graph.json"
    lineage_graph_path = CARTOGRAPHY_DIR / "lineage_graph.json"

    kg.serialize_module_graph(str(module_graph_path))
    kg.serialize_lineage_graph(str(lineage_graph_path))

    print(f"Module graph saved to {module_graph_path}")
    print(f"Lineage graph saved to {lineage_graph_path}")

    # 4️⃣ Run Semanticist → insights
    print("\n" + "*" * 40 + " Running Semanticist " + "*" * 60 + "\n")
    semanticist.analyze_repo()  # generate purpose statements and cluster domains
    day_one_answers = semanticist.answer_day_one_questions()  # synthesize answers

    print("\nFive FDE Day-One Answers:\n")
    print(day_one_answers)

    # 5️⃣ Run Archivist → generate artifacts
    print("\n" + "*" * 40 + " Running Archivist " + "*" * 60 + "\n")

    # ---------- Decide on Archivist run ----------
    if is_first_run or changed_files:
        if is_first_run:
            print("First run — generating all artifacts...")
            archivist.serialize_lineage_graph()
            codebase_path = archivist.generate_CODEBASE_md()
            brief_path = archivist.generate_onboarding_brief()
            semantic_index_dir = archivist.build_semantic_index()

            print(f"CODEBASE.md written to {codebase_path}")
            print(f"Onboarding brief written to {brief_path}")
            print(f"Semantic index stored in {semantic_index_dir}")
        else:
            print(f"Detected {len(changed_files)} changed files — running incremental update...")
            archivist.incremental_update(changed_files)
    else:
        print("No changes detected — skipping Archivist update")


    # 6️⃣ Navigator interactive section
    # ------------------------------
    print("\n" + "*" * 40 + " Navigator Interactive " + "*" * 60 + "\n")

    tools = {
        "1": "find_implementation",
        "2": "trace_lineage",
        "3": "blast_radius",
        "4": "explain_module",
        "q": "quit"
    }

    print("Navigator Tools:")
    print("1: find_implementation")
    print("2: trace_lineage")
    print("3: blast_radius")
    print("4: explain_module")
    print("q: quit")

    while True:
        choice = input("\nSelect a tool (1-4) or 'q' to quit: ").strip()
        if choice == "q":
            break
        if choice not in tools:
            print("Invalid choice")
            continue

        tool_name = tools[choice]

        if tool_name == "find_implementation":
            concept = input("Enter concept to search for: ").strip()
            top_k = int(input("Top k modules to return [5]: ") or 5)
            results = navigator.find_implementation(concept, top_k=top_k)
            print("\nMatches:", results)

        elif tool_name == "trace_lineage":
            dataset = input("Enter dataset/module name: ").strip()
            direction = input("Direction (upstream/downstream) [upstream]: ").strip() or "upstream"
            results = navigator.trace_lineage(dataset, direction=direction)
            print("\nLineage:", results)

        elif tool_name == "blast_radius":
            module_path = input("Enter module path: ").strip()
            results = navigator.blast_radius(module_path)
            print("\nAffected modules:", results)

        elif tool_name == "explain_module":
            module_path = input("Enter module path: ").strip()
            result = navigator.explain_module(module_path)
            print("\nModule Explanation:\n", result)
