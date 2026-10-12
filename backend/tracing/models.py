from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class TraceStep(BaseModel):
    step_number: int
    symbol: str
    type: Optional[str] = None
    file: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    relationship: str = "calls"
    evidence: Optional[str] = None

class ExecutionTrace(BaseModel):
    entrypoint: str
    steps: List[TraceStep] = Field(default_factory=list)
    confidence: str = "high"  # 'high', 'medium', 'low', 'unresolved'
    unresolved_steps: List[str] = Field(default_factory=list)
    alternative_paths: List[List[TraceStep]] = Field(default_factory=list)
    explanation: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TraceRequest(BaseModel):
    repo_id: str
    entrypoint: Optional[str] = None
    query: Optional[str] = None
    target: Optional[str] = None
    max_depth: int = 8
