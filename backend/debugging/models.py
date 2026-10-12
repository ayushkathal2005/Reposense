from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class FailureLocation(BaseModel):
    file: str
    line: Optional[int] = None
    symbol: Optional[str] = None
    code_snippet: Optional[str] = None
    relevance_score: float = 1.0

class DebugEvidenceItem(BaseModel):
    category: str  # 'FACT', 'INFERENCE', 'POSSIBLE_CAUSE', 'RECOMMENDED_FIX'
    statement: str
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    symbol: Optional[str] = None

class DebugAnalysisResponse(BaseModel):
    error_summary: str
    likely_locations: List[FailureLocation] = Field(default_factory=list)
    facts: List[str] = Field(default_factory=list)
    inferences: List[str] = Field(default_factory=list)
    possible_causes: List[str] = Field(default_factory=list)
    possible_fixes: List[str] = Field(default_factory=list)
    related_callers: List[str] = Field(default_factory=list)
    confidence: str = "Medium"  # 'High', 'Medium', 'Low'
    explanation: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DebugRequest(BaseModel):
    repo_id: str
    error_message: str
    stack_trace: Optional[str] = None
    file_path: Optional[str] = None
    symbol: Optional[str] = None
