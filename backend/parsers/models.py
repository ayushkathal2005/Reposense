from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Symbol(BaseModel):
    type: str  # 'function', 'class', 'method', 'import', 'route', 'variable', 'interface', 'type', 'file'
    name: str
    file: str
    language: Optional[str] = None
    start_line: int
    end_line: int
    signature: Optional[str] = None
    content: Optional[str] = None
    calls: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)  # for imports or inheritance
    docstring: Optional[str] = None
    decorators: List[str] = Field(default_factory=list)
    route_path: Optional[str] = None
    route_method: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def file_path(self) -> str:
        return self.file
