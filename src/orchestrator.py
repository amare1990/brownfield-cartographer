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
import sys

# ----------------------------
# Setup
# ----------------------------
CARTOGRAPHY_DIR = Path.cwd() / ".cartography"
CARTOGRAPHY_DIR.mkdir(exist_ok=True)

# Knowledge Graph
kg = KnowledgeGraph()

# TreeSitter Analyzer
ts_analyzer = TreeSitterAnalyzer()

# Agents
surveyor = Surveyor(kg, ts_analyzer)
hydrologist = Hydrologist(kg, ts_analyzer)
semanticist = Semanticist(kg)
archivist = Archivist(
    kg=kg,
    surveyor=surveyor,
    hydrologist=hydrologist,
    semanticist=semanticist,
    artifacts_dir=CARTOGRAPHY_DIR
)
archivist.build_semantic_index()
navigator = Navigator(kg, semanticist, hydrologist, archivist)

# Python Parser for Hydrologist
PY_LANGUAGE = Language(tspython.language())
python_parser = Parser(PY_LANGUAGE)

# ----------------------------
# Repository Helpers
# ----------------------------
def clone_repo_if_needed(repo_path: str) -> str:
    if repo_path.startswith("http"):
        print(f"Cloning GitHub repo {repo_path} ...")
        tmp = tempfile.mkdtemp()
        subprocess.run(["git", "clone", repo_path, tmp])
        print(f"Repository cloned to temporary path: {tmp}")
        return tmp
    return repo_path

def get_changed_files(repo_path: str, commit_range: str = "HEAD~1..HEAD") -> list[str]:
    """Return list of changed files for incremental updates based on commits."""
    try:
        result = check_output(["git", "diff", "--name-only", commit_range], cwd=repo_path)
        files = result.decode().splitlines()
        print(f"Changed files detected ({len(files)}): {files}")
        return files
    except Exception as e:
        print(f"Failed to get changed files: {e}")
        return []

# ----------------------------
# Core Orchestration
# ----------------------------
def run_repo_analysis(repo_path: str):
    repo_path = clone_repo_if_needed(repo_path)
    repo_path_obj = Path(repo_path)
    changed_files = get_changed_files(str(repo_path_obj))
    is_first_run = not (CARTOGRAPHY_DIR / "CODEBASE.md").exists()

    # 1️⃣ Surveyor → module graph
    try:
        print("\n" + "*" * 40 + " Running Surveyor " + "*" * 60 + "\n")
        surveyor.analyze_repo(str(repo_path_obj))
        print(f"Module graph nodes: {len(kg.module_graph.nodes)}")
        print(f"Module graph edges: {len(kg.module_graph.edges)}")

        print("\n" + "*" * 40 + " Graph Analytics " + "*" * 60 + "\n")
        hubs = surveyor.find_architectural_hubs()
        cycles = surveyor.detect_cycles()
        dead_code = surveyor.detect_dead_code()
        print(f"Top architectural hubs: {hubs[:5]}")
        print(f"Circular dependencies: {cycles}")
        print(f"Dead code candidates: {dead_code[:10]}")

    finally:
        # Serialize module graph even if errors occur
        kg.serialize_module_graph(str(CARTOGRAPHY_DIR / "module_graph.json"))

    # 2️⃣ Hydrologist → lineage graph
    try:
        print("\n" + "*" * 40 + " Running Hydrologist " + "*" * 60 + "\n")
        print("Running Hydrologist (data lineage analysis)...")
        hydrologist.analyze_repo(str(repo_path_obj))
        print(f"Lineage graph nodes: {len(kg.lineage_graph.nodes)}")
        print(f"Lineage graph edges: {len(kg.lineage_graph.edges)}")

        print("\n" + "*" * 40 + " Hydrologist Lineage Edges " + "*" * 60 + "\n")
        for source, target, metadata in kg.lineage_graph.edges(data=True):
            edge_type = metadata.get("edge_type", "unknown")
            print(f"{source} -> {target} | type={edge_type} | metadata={metadata}")


    finally:
        kg.serialize_lineage_graph(str(CARTOGRAPHY_DIR / "lineage_graph.json"))

    # 3️⃣ Semanticist → purpose statements / clustering
    try:
        print("\n" + "*" * 40 + " Running Semanticist " + "*" * 60 + "\n")
        semanticist.analyze_repo()
        day_one_answers = semanticist.answer_day_one_questions()
        print("\nFive FDE Day-One Answers:\n")
        print(day_one_answers)
    except Exception as e:
        print(f"Semanticist failed: {e}")

    # 4️⃣ Archivist → artifacts
    try:
        print("\n" + "*" * 40 + " Running Archivist " + "*" * 60 + "\n")
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
    except Exception as e:
        print(f"Archivist failed: {e}")

# ----------------------------
# Navigator CLI
# ----------------------------
def navigator_cli(navigator):
    print("\n--- Navigator Interactive Mode ---")
    print("Tools:")
    print("1: find_implementation")
    print("2: trace_lineage")
    print("3: blast_radius")
    print("4: explain_module")
    print("q: quit")

    while True:
        choice = input("\nSelect a tool (1-4) or 'q' to quit: ").strip()
        if choice == "q":
            break
        if choice not in {"1","2","3","4"}:
            print("Invalid choice")
            continue

        if choice == "1":
            concept = input("Enter concept to search for: ").strip()
            top_k = int(input("Top k modules to return [5]: ") or 5)
            results = navigator.find_implementation(concept, top_k=top_k)
            for i, module in enumerate(results, 1):
                print(f"{i}. {module}")

        elif choice == "2":
            dataset = input("Enter dataset/module name: ").strip()
            direction = input("Direction (upstream/downstream) [upstream]: ").strip() or "upstream"
            results = navigator.trace_lineage(dataset, direction=direction)
            if not results:
                print("No lineage found.")
                continue
            for entry in results:
                lines = entry.get("lines", (None, None))
                print(f"- {entry['module']} | source={entry['source']} | lines={lines[0]}-{lines[1]}")

        elif choice == "3":
            module_path = input("Enter module path: ").strip()
            results = navigator.blast_radius(module_path)
            print("Affected modules:", results)

        elif choice == "4":
            module_path = input("Enter module path: ").strip()
            result = navigator.explain_module(module_path)
            print("\nModule Explanation:\n", result)

