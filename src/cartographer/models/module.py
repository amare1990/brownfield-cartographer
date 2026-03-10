from pydantic import BaseModel
from typing import Optional

class ModuleNode(BaseModel):
    path: str
    language: str
    complexity_score: Optional[float] = None
    change_velocity_30d: Optional[int] = None
    is_dead_code_candidate: bool = False
