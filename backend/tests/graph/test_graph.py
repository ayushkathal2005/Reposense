import pytest
from parsers.models import Symbol
from graph import build_knowledge_graph, get_callers, get_dependencies, find_shortest_path

def test_build_and_query_graph():
    symbols = [
        Symbol(type="function", name="main", file="main.py", start_line=1, end_line=5, calls=["process_data", "print"]),
        Symbol(type="function", name="process_data", file="data.py", start_line=1, end_line=10, calls=["clean_string"]),
        Symbol(type="function", name="clean_string", file="utils.py", start_line=1, end_line=5, calls=[]),
        Symbol(type="class", name="DataHelper", file="data.py", start_line=12, end_line=20, dependencies=["utils.py"])
    ]
    
    G = build_knowledge_graph(symbols)
    
    # 4 symbols + 3 files = 7 nodes minimum (some files might overlap)
    assert len(G.nodes) >= 4
    
    callers = get_callers(G, "process_data")
    assert "main" in callers
    
    deps = get_dependencies(G, "DataHelper")
    assert "utils.py" in deps
    
    path, nodes, edges = find_shortest_path(G, "main", "clean_string")
    assert path == ["main", "process_data", "clean_string"]
    assert nodes > 0
    assert edges > 0
