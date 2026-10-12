import pytest
import networkx as nx
from schemas import (
    AnalysisResponse,
    EvidenceItem,
    ExecutionTraceResponse,
    ImpactAnalysisResponse,
    DebugAnalysisResponse,
    DocumentationResponse,
)
from query.engine import QueryEngine
from query.llm import LLMClient
from indexing.models import SymbolRecord

class MockLLM(LLMClient):
    def __init__(self):
        pass

    def generate(self, prompt: str) -> str:
        return "Synthesized answer with verified evidence."

def mock_search_similar_symbols(db, text, top_k=3, repo_id=None):
    sym = SymbolRecord(
        id=1,
        name="authenticate",
        file_path="src/auth.py",
        start_line=10,
        end_line=25,
        docstring="Authenticates user session"
    )
    return [(sym, 0.95)]


def test_analysis_response_schema_fields():
    resp = AnalysisResponse(
        answer="Order created successfully.",
        confidence="high",
        evidence=[
            EvidenceItem(file="src/orders.py", line=42, symbol="create_order")
        ],
        related_symbols=["create_order", "OrderController"],
        source_references=["src/orders.py:42-50"],
        warnings=[],
        unresolved=[],
        sources=[{"name": "create_order", "file": "src/orders.py"}],
        prompt="User Query: create order"
    )

    # Test object attribute access
    assert resp.answer == "Order created successfully."
    assert resp.confidence == "high"
    assert len(resp.evidence) == 1
    assert resp.evidence[0].file == "src/orders.py"
    assert resp.evidence[0].line == 42
    assert resp.evidence[0].symbol == "create_order"
    assert "create_order" in resp.related_symbols

    # Test backwards-compatible dictionary subscript access
    assert resp["answer"] == "Order created successfully."
    assert len(resp["sources"]) == 1
    assert resp["prompt"] == "User Query: create order"

    # Test JSON serialization
    serialized = resp.model_dump()
    assert "evidence" in serialized
    assert "confidence" in serialized


def test_query_engine_returns_structured_analysis_response(monkeypatch):
    monkeypatch.setattr('query.context_builder.search_similar_symbols', mock_search_similar_symbols)

    graph = nx.DiGraph()
    graph.add_node("authenticate")
    graph.add_edge("authenticate", "db.query", relationship="calls")

    engine = QueryEngine(db=None, graph=graph, llm=MockLLM())
    result = engine.query("How does authentication work?")

    assert isinstance(result, AnalysisResponse)
    assert result.confidence == "high"
    assert len(result.evidence) >= 1
    assert result.evidence[0].symbol == "authenticate"
    assert result.evidence[0].file == "src/auth.py"
    assert result.evidence[0].line == 10
    assert "src/auth.py:10-25" in result.source_references
    assert "authenticate" in result.related_symbols

    # Backwards compatibility check
    assert result["answer"] == "Synthesized answer with verified evidence."
    assert len(result["sources"]) == 1


def test_standardized_response_schemas_export():
    assert AnalysisResponse is not None
    assert ExecutionTraceResponse is not None
    assert ImpactAnalysisResponse is not None
    assert DebugAnalysisResponse is not None
    assert DocumentationResponse is not None
