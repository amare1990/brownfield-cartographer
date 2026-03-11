import os
import ast
import yaml
from pathlib import Path
from typing import List, Dict

class DAGConfigAnalyzer:
    @staticmethod
    def parse_dbt_schema(schema_path: str) -> Dict[str, List[str]]:
        """Return mapping: model -> upstream dependencies"""
        with open(schema_path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
        lineage = {}
        for model_name, model_info in content.get("models", {}).items():
            upstream = model_info.get("depends_on", [])
            lineage[model_name] = upstream
        return lineage

    @staticmethod
    def parse_airflow_dag(dag_path: str) -> Dict[str, List[str]]:
        """Extract tasks and their dependencies"""
        with open(dag_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=dag_path)

        deps: Dict[str, List[str]] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                target = node.targets[0]
                # Only access id if target is ast.Name
                if isinstance(target, ast.Name):
                    task_name = target.id
                    deps[task_name] = []
            elif isinstance(node, ast.Call):
                func_attr = getattr(node.func, 'attr', None)
                if func_attr in {"set_downstream", "set_upstream"}:
                    # TODO: extract dependencies
                    pass

        return deps
