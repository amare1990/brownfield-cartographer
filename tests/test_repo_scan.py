from pathlib import Path
from cartographer.analyzers.repo_inventory import scan_repository


def test_repo_scan():
    repo = Path("data/sample_repos/jaffle_shop")

    inventory = scan_repository(repo)

    assert len(inventory.files) > 0
