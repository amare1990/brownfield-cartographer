import typer
from orchestrator import run_analysis

app = typer.Typer()

@app.command()
def analyze(repo_path: str):
    run_analysis(repo_path)


if __name__ == "__main__":
    app()
