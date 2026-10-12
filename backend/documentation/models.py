from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SymbolDoc(BaseModel):
    name: str
    type: Optional[str] = None
    file: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    signature: Optional[str] = None
    docstring: Optional[str] = None
    callers: List[str] = Field(default_factory=list)
    callees: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    evidence_sources: List[str] = Field(default_factory=list)

class DocumentationResponse(BaseModel):
    title: str
    doc_type: str  # 'api', 'function', 'module', 'architecture'
    target: str
    markdown_content: str
    symbols: List[SymbolDoc] = Field(default_factory=list)
    diagram_mermaid: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocRequest(BaseModel):
    repo_id: str
    target: Optional[str] = None
    doc_type: str = "api"  # 'api', 'function', 'module', 'architecture'
