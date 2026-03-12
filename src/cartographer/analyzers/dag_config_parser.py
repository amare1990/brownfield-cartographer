# src/cartographer/analyzers/dag_config_parser.py

import os
import ast
import yaml
from pathlib import Path
from typing import List, Dict, Union


class DAGConfigAnalyzer:
    def parse_dbt_schema(self, schema_path: str) -> Dict[str, List[str]]:
        """
        Extract dbt model dependencies from a YAML schema file.
        Handles both styles:
          - models: [{name: "model1", depends_on: ["other_model"]}, ...]
          - models: ["model1", "model2", ...]
        Returns: dict where keys are model names and values are list of upstream dependencies
        """
        with open(schema_path, "r", encoding="utf-8") as f:
            content: Dict[str, Union[List, Dict]] = yaml.safe_load(f) or {}

        lineage: Dict[str, List[str]] = {}
        models_list = content.get("models", [])

        for model_info in models_list:
            if isinstance(model_info, dict):
                model_name = model_info.get("name")
                if not model_name:
                    continue
                upstream = model_info.get("depends_on", [])
            elif isinstance(model_info, str):
                # Model is just a string, assume no dependencies
                model_name = model_info
                upstream = []
            else:
                # Unexpected type, skip
                continue

            lineage[model_name] = upstream

        return lineage

    @staticmethod
    def parse_airflow_dag(dag_path: str) -> Dict[str, List[str]]:
        """Extract tasks and their dependencies from an Airflow DAG Python file"""
        with open(dag_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=dag_path)

        deps: Dict[str, List[str]] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                target = node.targets[0]
                if isinstance(target, ast.Name):
                    task_name = target.id
                    deps[task_name] = []
            elif isinstance(node, ast.Call):
                func_attr = getattr(node.func, "attr", None)
                if func_attr in {"set_downstream", "set_upstream"}:
                    # TODO: implement extraction of dependencies
                    pass

        return deps
