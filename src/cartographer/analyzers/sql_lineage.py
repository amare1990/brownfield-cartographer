# src/cartographer/analyzers/sql_lineage.py
import sqlglot
from sqlglot import parse_one, exp
from src.cartographer.models.lineage import EdgeType
from src.cartographer.graph.knowledge_graph import KnowledgeGraph

class SQLLineageAnalyzer:
    """Extracts SQL table dependencies via sqlglot with dynamic EdgeType."""

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg

    def analyze_sql_file(self, file_path: str, sql_text: str):
        try:
            tree = parse_one(sql_text)
        except Exception:
            # Skip invalid SQL
            return

        # Find all table references in FROM, JOIN, CTEs
        source_tables = [t.name for t in tree.find_all(exp.Table)]

        # Guess the output dataset (if any)
        output_table = self._guess_output_table(tree)

        # Determine edge type dynamically
        if output_table:
            edge_type = EdgeType.PRODUCES
            self.kg.add_dataset(output_table, storage_type="table")
        else:
            edge_type = EdgeType.CONSUMES  # read-only query, no target dataset

        # Register source datasets
        for src in source_tables:
            self.kg.add_dataset(src, storage_type="table")

            if output_table:
                # Normal case: source -> target
                self.kg.add_lineage_edge(
                    source=src,
                    target=output_table,
                    edge_type=edge_type,
                    metadata={"source_file": str(file_path)}
                )
            else:
                # Read-only query, mark source as consumed by this query "pseudo-node"
                pseudo_target = f"query:{file_path}"
                self.kg.add_dataset(pseudo_target, storage_type="stream")
                self.kg.add_lineage_edge(
                    source=src,
                    target=pseudo_target,
                    edge_type=EdgeType.CONSUMES,
                    metadata={"source_file": str(file_path)}
                )

        # Detect function/procedure calls
        for func in tree.find_all(exp.Func):
            func_name = func.name
            pseudo_target = f"function:{func_name}"
            self.kg.add_dataset(pseudo_target, storage_type="stream")
            for src in source_tables:
                self.kg.add_lineage_edge(
                    source=src,
                    target=pseudo_target,
                    edge_type=EdgeType.CALLS,
                    metadata={"source_file": str(file_path)}
                )

        # Optional: detect configuration / pipeline updates
        for cfg in tree.find_all(exp.Set):
            cfg_name = cfg.name
            pseudo_target = f"config:{cfg_name}"
            self.kg.add_dataset(pseudo_target, storage_type="stream")
            for src in source_tables:
                self.kg.add_lineage_edge(
                    source=src,
                    target=pseudo_target,
                    edge_type=EdgeType.CONFIGURES,
                    metadata={"source_file": str(file_path)}
                )

    def _guess_output_table(self, tree):
        """
        Detects the output table from CREATE statements.
        If none found, returns None.
        """
        for node in tree.find_all(exp.Create):
            # exp.Create.this may be an expression representing table name
            if hasattr(node.this, "name"):
                return node.this.name
        return None
