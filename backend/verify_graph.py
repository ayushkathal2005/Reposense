import json
import networkx as nx
from pathlib import Path
from parsers import parse_file
from graph import build_knowledge_graph, find_shortest_path

def get_python_files(root_dir: Path):
    for path in root_dir.rglob("*.py"):
        if "venv" not in path.parts and "tests" not in path.parts:
            yield path

def main():
    root_dir = Path.cwd()
    symbols = []
    
    for py_file in get_python_files(root_dir):
        rel_path = str(py_file.relative_to(root_dir)).replace("\\", "/")
        file_symbols = parse_file(py_file, rel_path)
        symbols.extend(file_symbols)
        
    G = build_knowledge_graph(symbols)
    
    print(f"Graph created with {len(G.nodes)} nodes and {len(G.edges)} edges.\\n")
    
    # Try to find a path from ingest_repo (in main.py) to clone_repository (in git_client.py)
    # Wait, main.py -> ingest_repo -> ingest_repository -> clone_repository
    # ingest_repo is the function in main.py
    
    source = "ingest_repo"
    target = "clone_repository"
    
    path, nodes, edges = find_shortest_path(G, source, target)
    
    print(f"Shortest path from '{source}' to '{target}':")
    if path:
        print(" -> ".join(path))
    else:
        print("No path found.")
        
    print(f"\\nStats: {nodes} total nodes, {edges} total edges in undirected evaluation graph.")

if __name__ == "__main__":
    main()
