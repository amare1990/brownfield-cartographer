from pathlib import Path
from typing import List


class TreeSitterAnalyzer:

    def extract_imports(self, file_path: Path) -> List[str]:
        """
        Extract import statements from python files.
        """
        imports = []

        with open(file_path) as f:
            for line in f:
                if line.startswith("import") or line.startswith("from"):
                    imports.append(line.strip())

        return imports
