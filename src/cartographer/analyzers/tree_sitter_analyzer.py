import os
from pathlib import Path
from typing import List, Optional, Dict
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_sql as tssql
import tree_sitter_yaml as tsyaml
import tree_sitter_javascript as tsjs
import tree_sitter_typescript as tsts

from src.cartographer.models.node import ModuleNode

# ----- Language Configurations -----
LANGUAGES = {
    "python": Language(tspython.language()),
    "sql": Language(tssql.language()),
    "yaml": Language(tsyaml.language()),
    "javascript": Language(tsjs.language()),
    "typescript": Language(tsts.language_typescript()),
}

class LanguageRouter:
    EXTENSION_MAP = {
        ".py": "python",
        ".sql": "sql",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".js": "javascript",
        ".ts": "typescript",
    }

    @classmethod
    def get_language(cls, file_path: str) -> Optional[str]:
        ext = Path(file_path).suffix.lower()
        return cls.EXTENSION_MAP.get(ext)

class TreeSitterAnalyzer:
    def __init__(self):
        """Initialize a dedicated Parser for each supported language."""
        # In Tree-sitter 0.22+, we pass the language directly to the Parser constructor
        self.parsers: Dict[str, Parser] = {
            name: Parser(lang_obj) for name, lang_obj in LANGUAGES.items()
        }

    def get_tree(self, file_path: str):
        """Helper for agents to get a parsed AST for any supported file."""
        lang_name = LanguageRouter.get_language(file_path)
        if not lang_name or lang_name not in self.parsers:
            return None

        parser = self.parsers[lang_name]
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code_bytes = f.read().encode("utf-8")
            return parser.parse(code_bytes)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None

    def analyze_module(self, file_path: str) -> ModuleNode:
        """Create a ModuleNode skeleton and identify language."""
        language = LanguageRouter.get_language(file_path)
        if not language:
            raise ValueError(f"Unsupported file extension: {file_path}")

        # The tree is available here if you want to perform immediate extraction
        tree = self.get_tree(file_path)

        # Placeholder: In the future, you can use `tree` with Tree-sitter Queries
        # to populate purpose_statement or complexity scores automatically.

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
