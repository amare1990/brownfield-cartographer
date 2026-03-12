import typer
from src.orchestrator import run_repo_analysis

app = typer.Typer()

@app.command()
def analyze(repo_path: str):
    run_repo_analysis(repo_path)


if __name__ == "__main__":
    app()
