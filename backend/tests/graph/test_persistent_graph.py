import pytest
import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from indexing.models import Base
from parsers.models import Symbol
from graph.builder import build_knowledge_graph
from graph.store import save_graph, load_graph, get_or_load_graph, inspect_graph, clear_graph_cache
from graph.queries import get_callers, get_dependencies

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    clear_graph_cache()

def test_graph_persistence_survives_cache_clear(db_session):
    symbols = [
        Symbol(type="function", name="login", file="auth.py", start_line=1, end_line=10, calls=["verify_password"]),
        Symbol(type="function", name="verify_password", file="auth.py", start_line=11, end_line=20),
    ]
    graph = build_knowledge_graph(symbols, repo_id="my_repo")
    
    # 1. Save to DB
    save_graph(db_session, "my_repo", graph)
    
    # 2. Simulate server restart by clearing in-memory cache
    clear_graph_cache()
    
    # 3. Load from DB
    loaded_graph = load_graph(db_session, "my_repo")
    assert loaded_graph is not None
    assert "login" in loaded_graph
    assert "verify_password" in loaded_graph
    assert "auth.py" in loaded_graph
    assert "my_repo" in loaded_graph
    
    callers = get_callers(loaded_graph, "verify_password")
    assert "login" in callers

def test_graph_node_types_and_relationships():
    symbols = [
        Symbol(type="class", name="UserModel", file="models.py", start_line=1, end_line=30, dependencies=["BaseModel"]),
        Symbol(type="method", name="UserModel.get_id", file="models.py", start_line=10, end_line=15),
        Symbol(type="route", name="get_users", file="api.py", start_line=5, end_line=12, route_path="/api/users", route_method="GET"),
    ]
    graph = build_knowledge_graph(symbols, repo_id="app_repo")
    
    # Check node types
    assert graph.nodes["app_repo"]["type"] == "repository"
    assert graph.nodes["models.py"]["type"] == "file"
    assert graph.nodes["UserModel"]["type"] == "database_model"
    assert graph.nodes["get_users"]["type"] == "endpoint"
    assert graph.nodes["get_users"]["route_path"] == "/api/users"
    
    # Check relationships
    edge_rels = {(u, v): d.get("relationship") for u, v, d in graph.edges(data=True)}
    assert edge_rels.get(("app_repo", "models.py")) == "contains"
    assert edge_rels.get(("models.py", "UserModel")) == "defines"
    assert edge_rels.get(("UserModel", "models.py")) == "defined_in"
    assert edge_rels.get(("UserModel", "UserModel.get_id")) == "contains"
    assert edge_rels.get(("api.py", "get_users")) == "exposes"

def test_reingestion_updates_graph(db_session):
    syms_v1 = [Symbol(type="function", name="fn1", file="a.py", start_line=1, end_line=5)]
    g1 = build_knowledge_graph(syms_v1, repo_id="update_repo")
    save_graph(db_session, "update_repo", g1)
    
    clear_graph_cache()
    loaded_v1 = get_or_load_graph(db_session, "update_repo")
    assert "fn1" in loaded_v1
    assert "fn2" not in loaded_v1
    
    # Re-ingest with new symbols
    syms_v2 = [
        Symbol(type="function", name="fn1", file="a.py", start_line=1, end_line=5),
        Symbol(type="function", name="fn2", file="a.py", start_line=6, end_line=10)
    ]
    g2 = build_knowledge_graph(syms_v2, repo_id="update_repo")
    save_graph(db_session, "update_repo", g2)
    
    clear_graph_cache()
    loaded_v2 = get_or_load_graph(db_session, "update_repo")
    assert "fn1" in loaded_v2
    assert "fn2" in loaded_v2
    assert loaded_v2.number_of_nodes() > loaded_v1.number_of_nodes()

def test_inspect_graph():
    symbols = [
        Symbol(type="function", name="fetch_data", file="client.py", start_line=1, end_line=10, calls=["parse"]),
        Symbol(type="function", name="parse", file="client.py", start_line=11, end_line=20)
    ]
    graph = build_knowledge_graph(symbols, repo_id="test_inspect")
    
    inspection = inspect_graph(graph)
    assert inspection["node_count"] > 0
    assert inspection["edge_count"] > 0
    assert "node_types" in inspection
    assert "nodes" in inspection
    assert "edges" in inspection
    assert any(n["name"] == "fetch_data" for n in inspection["nodes"])
    assert any(e["source"] == "fetch_data" and e["target"] == "parse" for e in inspection["edges"])
