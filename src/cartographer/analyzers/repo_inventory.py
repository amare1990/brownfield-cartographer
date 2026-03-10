from pathlib import Path
from typing import List
from pydantic import BaseModel


class RepoFile(BaseModel):
    path: str
    language: str


class RepoInventory(BaseModel):
    root_path: str
    files: List[RepoFile]


def scan_repository(repo_path: Path) -> RepoInventory:
    files = []

    for path in repo_path.rglob("*"):
        if path.is_file():
            ext = path.suffix.lower()

            if ext == ".py":
                lang = "python"
            elif ext == ".sql":
                lang = "sql"
            elif ext in [".yml", ".yaml"]:
                lang = "yaml"
            else:
                lang = "other"

            files.append(
                RepoFile(
                    path=str(path),
                    language=lang,
                )
            )

    return RepoInventory(
        root_path=str(repo_path),
        files=files,
    )
