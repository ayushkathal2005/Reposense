import networkx as nx
from typing import List, Tuple

def get_callers(G: nx.DiGraph, target: str) -> List[str]:
    if target not in G:
        return []
    return [u for u, v, data in G.in_edges(target, data=True) if data.get('relationship') == 'calls']

def get_dependencies(G: nx.DiGraph, target: str) -> List[str]:
    if target not in G:
        return []
    return [v for u, v, data in G.out_edges(target, data=True) if data.get('relationship') == 'depends_on']

def find_shortest_path(G: nx.DiGraph, source: str, target: str) -> Tuple[List[str], int, int]:
    try:
        # We use undirected graph to find ANY link for "distant components path" 
        U = G.to_undirected()
        path = nx.shortest_path(U, source=source, target=target)
        
        num_nodes = len(G.nodes)
        num_edges = len(G.edges)
        
        return path, num_nodes, num_edges
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return [], len(G.nodes), len(G.edges)
