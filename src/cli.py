# src/cli.py
import typer
from src.orchestrator import run_repo_analysis, navigator_cli, navigator  # import navigator directly

app = typer.Typer()

@app.command()
def analyze(repo_path: str):
    """Run full repo analysis (Surveyor, Hydrologist, Semanticist, Archivist)."""
    run_repo_analysis(repo_path)

@app.command()
def nav():
    """Interactive Navigator CLI."""
    navigator_cli(navigator)

if __name__ == "__main__":
    app()
