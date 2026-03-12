from pydantic import BaseModel
from typing import List, Optional, Dict

class ModuleNode(BaseModel):
    path: str
    language: str
    purpose_statement: Optional[str]
    domain_cluster: Optional[str]
    complexity_score: Optional[float]
    change_velocity_30d: Optional[int]
    is_dead_code_candidate: Optional[bool]
    last_modified: Optional[str]

class DatasetNode(BaseModel):
    name: str
    storage_type: str  # table|file|stream|api
    schema_snapshot: Optional[Dict] = None
    freshness_sla: Optional[str] = None
    owner: Optional[str] = None
    is_source_of_truth: Optional[bool] = False

class FunctionNode(BaseModel):
    qualified_name: str
    parent_module: str
    signature: str
    purpose_statement: Optional[str] = None
    call_count_within_repo: Optional[int] = 0
    is_public_api: Optional[bool] = True

class TransformationNode(BaseModel):
    source_datasets: List[str]
    target_datasets: List[str]
    transformation_type: str
    source_file: str
    line_range: Optional[List[int]] = None
    sql_query_if_applicable: Optional[str] = None
