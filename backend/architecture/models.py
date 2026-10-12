from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ArchitectureComponent(BaseModel):
    id: str
    name: str
    role: str  # 'api', 'controller', 'service', 'repository', 'database', 'external_service', 'frontend', 'utility', 'module'
    file: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    docstring: Optional[str] = None
    symbols: List[str] = Field(default_factory=list)
    outgoing_calls: List[str] = Field(default_factory=list)

class ArchitectureRelationship(BaseModel):
    source: str
    target: str
    source_role: str
    target_role: str
    relationship: str = "calls"
    call_count: int = 1

class ArchitectureReport(BaseModel):
    components: List[ArchitectureComponent] = Field(default_factory=list)
    relationships: List[ArchitectureRelationship] = Field(default_factory=list)
    layers: Dict[str, List[str]] = Field(default_factory=dict)
    mermaid_diagram: str
    layer_diagram: str
    summary: Dict[str, Any] = Field(default_factory=dict)
