# SQL Lineage Analyzer using sqlglot
# This module defines the SQLLineageAnalyzer class, which uses the sqlglot library
# to parse SQL files and extract table dependencies. It integrates with the KnowledgeGraph
# to build a lineage graph of datasets based on SQL queries, identifying source tables
# and output tables for lineage analysis.

# SQL Lineage Analyzer using sqlglot
# src/cartographer/analyzers/sql_lineage.py

import sqlglot
from sqlglot import parse_one, exp
from src.cartographer.graph.knowledge_graph import KnowledgeGraph

class SQLLineageAnalyzer:
    """Extracts SQL table dependencies via sqlglot."""

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg

    def analyze_sql_file(self, file_path: str, sql_text: str):
        try:
            tree = parse_one(sql_text)
        except Exception:
            return  # skip invalid SQL

        # Extract tables used in FROM/JOIN/CTEs
        tables = [t.name for t in tree.find_all(exp.Table)]
        output_table = self._guess_output_table(tree)

        if output_table:
            self.kg.add_dataset(output_table)
            for t in tables:
                self.kg.add_dataset(t)
                self.kg.add_lineage(t, output_table, attrs={"source_file": file_path})

    def _guess_output_table(self, tree):
        # Minimal placeholder: real logic for CREATE TABLE / dbt model
        for node in tree.find_all(exp.Create):
            return node.this.name
        return None
