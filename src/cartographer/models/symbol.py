from pydantic import BaseModel
from typing import Optional

class SymbolInfo(BaseModel):
    name: str
    symbol_type: str  # function | class | variable
    module_path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
