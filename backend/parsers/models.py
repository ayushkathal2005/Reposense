from pydantic import BaseModel, Field
from typing import List, Optional

class Symbol(BaseModel):
    type: str # 'function', 'class', 'method', 'import', 'route', 'variable'
    name: str
    file: str
    start_line: int
    end_line: int
    calls: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list) # for imports or inheritance
    docstring: Optional[str] = None
    decorators: List[str] = Field(default_factory=list)
    route_path: Optional[str] = None
    route_method: Optional[str] = None
