from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class DependentItem(BaseModel):
    symbol: str
    type: Optional[str] = None
    file: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    relationship: str = "calls"
    depth: int = 1

class ImpactAnalysisResponse(BaseModel):
    target_symbol: str
    risk_level: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    risk_score: float = 0.0
    risk_factors: List[str] = Field(default_factory=list)
    direct_dependents: List[DependentItem] = Field(default_factory=list)
    indirect_dependents: List[DependentItem] = Field(default_factory=list)
    affected_files: List[str] = Field(default_factory=list)
    affected_apis: List[str] = Field(default_factory=list)
    affected_tests: List[str] = Field(default_factory=list)
    blast_radius_count: int = 0
    explanation: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ImpactRequest(BaseModel):
    repo_id: str
    symbol: str
    file_path: Optional[str] = None
    max_depth: int = 6
