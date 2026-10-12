from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class EvidenceItem(BaseModel):
    file: str
    line: Optional[int] = None
    symbol: Optional[str] = None
    snippet: Optional[str] = None

class AnalysisResponse(BaseModel):
    answer: str
    confidence: str = "high"  # "high", "medium", "low"
    evidence: List[EvidenceItem] = Field(default_factory=list)
    related_symbols: List[str] = Field(default_factory=list)
    source_references: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    unresolved: List[str] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    prompt: Optional[str] = None

    def __getitem__(self, item: str):
        """Allows dictionary subscript access for backwards compatibility."""
        return getattr(self, item)

    def __contains__(self, item: str):
        return hasattr(self, item)

# Centralize / standardize phase schemas
from tracing.models import ExecutionTrace as ExecutionTraceResponse
from impact.models import ImpactAnalysisResponse
from debugging.models import DebugAnalysisResponse
from documentation.models import DocumentationResponse

__all__ = [
    "EvidenceItem",
    "AnalysisResponse",
    "ExecutionTraceResponse",
    "ImpactAnalysisResponse",
    "DebugAnalysisResponse",
    "DocumentationResponse",
]
