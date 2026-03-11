from pydantic import BaseModel
from typing import List, Optional

class LineageEdge(BaseModel):
    source: str
    target: str
    edge_type: str  # IMPORTS | PRODUCES | CONSUMES | CALLS | CONFIGURES
    weight: Optional[int] = None
    metadata: Optional[dict] = None
