from enum import Enum

from pydantic import BaseModel
from typing import Optional


class EdgeType(str, Enum):
    IMPORTS = "IMPORTS"
    PRODUCES = "PRODUCES"
    CONSUMES = "CONSUMES"
    CALLS = "CALLS"
    CONFIGURES = "CONFIGURES"

class LineageEdge(BaseModel):
    source: str
    target: str
    edge_type: EdgeType  # IMPORTS | PRODUCES | CONSUMES | CALLS | CONFIGURES
    weight: Optional[int] = None
    metadata: Optional[dict] = None
