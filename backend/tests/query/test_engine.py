import pytest
import networkx as nx
from query.engine import QueryEngine
from query.llm import LLMClient
from indexing.models import SymbolRecord

class MockLLM(LLMClient):
    def __init__(self):
        pass  # Override __init__ so it doesn't instantiate genai.Client
        
    def generate(self, prompt: str) -> str:
        return f"Mock Synthesized Answer for: {prompt[:20]}..."

def mock_search_similar_symbols(db, text, top_k=3, repo_id=None):
    sym = SymbolRecord(
        id=1, 
        name="login", 
        file_path="auth.py", 
        start_line=10, 
        end_line=15, 
        docstring="Handles user login"
    )
    return [(sym, 0.99)]

def test_query_engine(monkeypatch):
    monkeypatch.setattr('query.engine.search_similar_symbols', mock_search_similar_symbols)
    
    db = None
    graph = nx.DiGraph()
    graph.add_node("login")
    graph.add_edge("login", "db.verify_user", relationship="calls")
    
    llm = MockLLM()
    engine = QueryEngine(db, graph, llm)
    
    result = engine.query("How does login work?")
    
    assert "Mock Synthesized Answer" in result["answer"]
    assert len(result["sources"]) == 1
    assert result["sources"][0]["name"] == "login"
    
    prompt = result["prompt"]
    assert "User Query: How does login work?" in prompt
    assert "login (File: auth.py, Lines: 10-15)" in prompt
    assert "db.verify_user" in prompt  # ensure related nodes are included
