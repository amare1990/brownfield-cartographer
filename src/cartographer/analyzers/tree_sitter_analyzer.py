from tree_sitter import Language, Parser
from pathlib import Path
import os
from typing import Optional
from src.cartographer.models.node import ModuleNode

# Path to compiled shared library
PARSERS_PATH = Path(__file__).parent / "parsers.so"

LANGUAGES = {
    "python": Language(str(PARSERS_PATH), "python"),  # type: ignore
    "sql": Language(str(PARSERS_PATH), "sql"),        # type: ignore
    "yaml": Language(str(PARSERS_PATH), "yaml"),      # type: ignore
    "javascript": Language(str(PARSERS_PATH), "javascript"),  # type: ignore
}

class LanguageRouter:
    EXTENSION_MAP = {
        ".py": "python",
        ".sql": "sql",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".js": "javascript",
        ".ts": "javascript",
    }

    @classmethod
    def get_language(cls, file_path: str) -> Optional[str]:
        ext = os.path.splitext(file_path)[1]
        return cls.EXTENSION_MAP.get(ext)

class TreeSitterAnalyzer:
    def __init__(self):
        self.parsers = {lang: Parser() for lang in LANGUAGES}
        for lang, parser in self.parsers.items():
            parser.set_language(LANGUAGES[lang])  # type: ignore

    def analyze_module(self, file_path: str) -> ModuleNode:
        language = LanguageRouter.get_language(file_path)
        if not language:
            raise ValueError(f"Unsupported file extension: {file_path}")

        parser = self.parsers[language]
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read().encode("utf-8")
        tree = parser.parse(code)

        # TODO: traverse AST and extract imports/functions/classes
        return ModuleNode(
            path=file_path,
            language=language,
            purpose_statement=None,
            domain_cluster=None,
            complexity_score=None,
            change_velocity_30d=None,
            is_dead_code_candidate=False,
            last_modified=None
        )
