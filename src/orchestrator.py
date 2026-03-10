from pathlib import Path
import json

from src.cartographer.agents.surveyor import Surveyor


def run_analysis(repo_path: str):

    surveyor = Surveyor()

    graph = surveyor.analyze_repo(Path(repo_path))

    output_path = ".cartography/module_graph.json"

    with open(output_path, "w") as f:
        json.dump(graph.to_dict(), f, indent=2)

    print(f"Module graph saved to {output_path}")
