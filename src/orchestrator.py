# src/orchestrator.py
from pathlib import Path
import json
import os

from src.cartographer.graph.knowledge_graph import KnowledgeGraph
from src.cartographer.agents.surveyor import Surveyor, extract_git_velocity
from src.cartographer.agents.hydrologist import Hydrologist
from tree_sitter import Language, Parser

# # CLI app
# app = typer.Typer()

# Ensure cartography output dir exists
CARTOGRAPHY_DIR = Path(".cartography")
CARTOGRAPHY_DIR.mkdir(exist_ok=True)


def run_analysis(repo_path: str):
    repo_path_obj = Path(repo_path)
    kg = KnowledgeGraph()

    # ----- Initialize Surveyor -----
    surveyor = Surveyor(kg)

    # Analyze repo structure
    for py_file in repo_path_obj.rglob("*.py"):
        surveyor.analyze_module(str(py_file))

    # Optional: extract git velocity
    velocity = extract_git_velocity(str(repo_path_obj))
    print("High-velocity files:", velocity)

    # Serialize module graph
    module_graph_path = CARTOGRAPHY_DIR / "module_graph.json"
    kg.serialize_module_graph(str(module_graph_path))
    print(f"Module graph saved to {module_graph_path}")

    # ----- Initialize Hydrologist -----
    PARSERS_PATH = Path(__file__).parent / "cartographer" / "parsers.so"
    PY_LANGUAGE = Language(str(PARSERS_PATH), "python")    # type: ignore
    python_parser = Parser()
    python_parser.set_language(PY_LANGUAGE)                # type: ignore

    hydrologist = Hydrologist(kg, python_parser)
    hydrologist.analyze_repo(str(repo_path_obj))

    # Serialize lineage graph
    lineage_graph_path = CARTOGRAPHY_DIR / "lineage_graph.json"
    kg.serialize_lineage_graph(str(lineage_graph_path))
    print(f"Lineage graph saved to {lineage_graph_path}")


# @app.command()
# def analyze(repo_path: str):
#     """Run full Cartographer analysis on a repo (structure + lineage)."""
#     run_analysis(repo_path)


# if __name__ == "__main__":
#     app()
