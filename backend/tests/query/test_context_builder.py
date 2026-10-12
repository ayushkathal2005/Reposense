import pytest
import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from indexing.models import Base, SymbolRecord
from query.context_builder import ContextBuilder

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Seed symbols
    sym1 = SymbolRecord(
        id=1,
        repository_name="test_repo",
        name="PaymentService",
        type="class",
        file_path="services/payment.py",
        start_line=10,
        end_line=50,
        docstring="Handles customer payment processing and stripe integration."
    )
    sym2 = SymbolRecord(
        id=2,
        repository_name="test_repo",
        name="process_payment",
        type="method",
        file_path="services/payment.py",
        start_line=25,
        end_line=40,
        docstring="Execute charge against credit card gateway."
    )
    sym3 = SymbolRecord(
        id=3,
        repository_name="test_repo",
        name="auth_service",
        type="module",
        file_path="auth/auth_service.py",
        start_line=1,
        end_line=80,
        docstring="Authentication and JWT verification helper functions."
    )
    db.add_all([sym1, sym2, sym3])
    db.commit()
    
    yield db
    db.close()

def test_exact_symbol_ranking(db_session, monkeypatch):
    # Mock vector search to return empty so we test exact & keyword logic cleanly
    monkeypatch.setattr('query.context_builder.search_similar_symbols', lambda db, q, top_k, repo_id: [])
    
    graph = nx.DiGraph()
    builder = ContextBuilder(db_session, graph, repo_id="test_repo")
    
    context = builder.get_context("Where is PaymentService implemented?")
    sources = context["sources"]
    assert len(sources) > 0
    # PaymentService should be ranked highest due to exact symbol match
    assert sources[0]["name"] == "PaymentService"
    assert "services/payment.py" in sources[0]["file"]

def test_path_retrieval(db_session, monkeypatch):
    monkeypatch.setattr('query.context_builder.search_similar_symbols', lambda db, q, top_k, repo_id: [])
    
    graph = nx.DiGraph()
    builder = ContextBuilder(db_session, graph, repo_id="test_repo")
    
    context = builder.get_context("What is in auth_service.py?")
    sources = context["sources"]
    assert len(sources) > 0
    assert sources[0]["name"] == "auth_service"
    assert "auth/auth_service.py" in sources[0]["file"]

def test_grounded_prompt_instructions(db_session, monkeypatch):
    monkeypatch.setattr('query.context_builder.search_similar_symbols', lambda db, q, top_k, repo_id: [])
    
    graph = nx.DiGraph()
    builder = ContextBuilder(db_session, graph, repo_id="test_repo")
    
    context = builder.get_context("How does payment processing work?")
    prompt = context["prompt"]
    
    # Grounded Gemini prompt assertions
    assert "RepoSense's repository analysis engine" in prompt
    assert "Never invent files, symbols, dependencies" in prompt
    assert "cannot establish this from the indexed repository" in prompt
    assert "PaymentService" in prompt

def test_deduplication(db_session, monkeypatch):
    sym = db_session.query(SymbolRecord).filter_by(id=1).first()
    # Mock vector search to return the same symbol that keyword search also finds
    monkeypatch.setattr('query.context_builder.search_similar_symbols', lambda db, q, top_k, repo_id: [(sym, 0.95)])
    
    graph = nx.DiGraph()
    builder = ContextBuilder(db_session, graph, repo_id="test_repo")
    
    candidates = builder.select_primary_symbols("PaymentService")
    deduped = builder.deduplicate(candidates)
    
    ids = [s.id for s, _ in deduped]
    assert len(ids) == len(set(ids))

def test_context_budget_enforcement(db_session):
    graph = nx.DiGraph()
    builder = ContextBuilder(db_session, graph, repo_id="test_repo")
    
    large_syms = [
        SymbolRecord(id=i, name=f"func_{i}", file_path=f"file_{i}.py", docstring="X" * 1000)
        for i in range(20)
    ]
    budget_syms, _ = builder.enforce_context_budget(large_syms, set(), max_chars=1500)
    assert len(budget_syms) < len(large_syms)
