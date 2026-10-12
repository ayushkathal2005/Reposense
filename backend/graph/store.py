from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import networkx as nx

from indexing.models import GraphRecord

# In-memory graph cache to avoid repeated deserialization within the process
_GRAPH_CACHE: Dict[str, nx.DiGraph] = {}

def save_graph(db: Session, repo_id: str, graph: nx.DiGraph) -> GraphRecord:
    """
    Persists a NetworkX DiGraph into the repository_graphs database table
    and caches it in memory.
    """
    graph_data = nx.node_link_data(graph)
    node_count = len(graph.nodes)
    edge_count = len(graph.edges)
    now = datetime.now(timezone.utc)

    record = db.query(GraphRecord).filter(GraphRecord.repository_name == repo_id).first()
    if record:
        record.graph_data = graph_data
        record.node_count = node_count
        record.edge_count = edge_count
        record.updated_at = now
    else:
        record = GraphRecord(
            repository_name=repo_id,
            graph_data=graph_data,
            node_count=node_count,
            edge_count=edge_count,
            created_at=now,
            updated_at=now
        )
        db.add(record)

    db.commit()
    db.refresh(record)

    _GRAPH_CACHE[repo_id] = graph
    return record

def load_graph(db: Session, repo_id: str) -> Optional[nx.DiGraph]:
    """
    Loads a persisted graph for a repository from memory cache or database.
    Survives server restarts by reading from the database.
    """
    if repo_id in _GRAPH_CACHE:
        return _GRAPH_CACHE[repo_id]

    if not db:
        return None

    record = db.query(GraphRecord).filter(GraphRecord.repository_name == repo_id).first()
    if not record or not record.graph_data:
        return None

    try:
        # Reconstruct NetworkX DiGraph from serialized JSON
        graph = nx.node_link_graph(record.graph_data, directed=True, multigraph=False)
        _GRAPH_CACHE[repo_id] = graph
        return graph
    except Exception as e:
        print(f"Error deserializing graph for {repo_id}: {e}")
        return None

def get_or_load_graph(db: Session, repo_id: str) -> nx.DiGraph:
    """
    Convenience method to retrieve the repository graph or an empty DiGraph if not found.
    """
    G = load_graph(db, repo_id)
    return G if G is not None else nx.DiGraph()

def inspect_graph(graph: nx.DiGraph, max_nodes: int = 150) -> Dict[str, Any]:
    """
    Inspects a knowledge graph and returns node/edge statistics and structures.
    """
    type_counts: Dict[str, int] = {}
    nodes_summary: List[Dict[str, Any]] = []
    edges_summary: List[Dict[str, Any]] = []

    for node_id, attrs in list(graph.nodes(data=True))[:max_nodes]:
        ntype = attrs.get("type", "unknown")
        type_counts[ntype] = type_counts.get(ntype, 0) + 1
        nodes_summary.append({
            "id": node_id,
            "name": attrs.get("name", str(node_id)),
            "type": ntype,
            "file": attrs.get("file"),
            "start_line": attrs.get("start_line"),
            "end_line": attrs.get("end_line")
        })

    for u, v, data in list(graph.edges(data=True))[:max_nodes]:
        edges_summary.append({
            "source": u,
            "target": v,
            "relationship": data.get("relationship", "relates_to")
        })

    return {
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
        "node_types": type_counts,
        "nodes": nodes_summary,
        "edges": edges_summary
    }

def clear_graph_cache(repo_id: Optional[str] = None) -> None:
    """
    Clears in-memory graph cache.
    """
    global _GRAPH_CACHE
    if repo_id:
        _GRAPH_CACHE.pop(repo_id, None)
    else:
        _GRAPH_CACHE.clear()
