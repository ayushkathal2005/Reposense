import networkx as nx
from typing import List, Optional
from parsers.models import Symbol

def build_knowledge_graph(symbols: List[Symbol], repo_id: Optional[str] = None) -> nx.DiGraph:
    """
    Constructs an evidence-backed directed knowledge graph representing repository
    structure, symbol definitions, calls, imports, inheritance, and endpoints.
    """
    G = nx.DiGraph()

    # 1. Root repository node
    if repo_id:
        G.add_node(repo_id, type="repository", name=repo_id)

    # 2. Nodes pass (files, classes, functions, methods, endpoints, database models)
    for sym in symbols:
        inferred_type = sym.type
        if sym.type == "class" and any("model" in str(d).lower() or "base" in str(d).lower() for d in sym.dependencies):
            inferred_type = "database_model"
        elif sym.type == "route" or sym.route_path:
            inferred_type = "endpoint"

        node_attrs = {
            "name": sym.name,
            "type": inferred_type,
            "file": sym.file,
            "start_line": sym.start_line,
            "end_line": sym.end_line,
        }
        if sym.docstring:
            node_attrs["docstring"] = sym.docstring[:300]
        if sym.route_path:
            node_attrs["route_path"] = sym.route_path
            node_attrs["route_method"] = sym.route_method or "GET"

        G.add_node(sym.name, **node_attrs)

        # File node
        if not G.has_node(sym.file):
            G.add_node(sym.file, type="file", file=sym.file, name=sym.file)
            if repo_id:
                G.add_edge(repo_id, sym.file, relationship="contains")

        # Symbol definitions
        G.add_edge(sym.file, sym.name, relationship="defines")
        G.add_edge(sym.name, sym.file, relationship="defined_in")

        # Class contains method
        if "." in sym.name and sym.type in ("method", "function"):
            parent_class = sym.name.split('.')[0]
            if G.has_node(parent_class):
                G.add_edge(parent_class, sym.name, relationship="contains")

        # Endpoint exposure
        if inferred_type == "endpoint":
            G.add_edge(sym.file, sym.name, relationship="exposes")

    # 3. Edges pass (calls, imports, inheritance, dependencies)
    name_lookup = {sym.name.split('.')[-1]: sym.name for sym in symbols}

    for sym in symbols:
        for dep in sym.dependencies:
            target = dep if dep in G else name_lookup.get(dep)
            if not target and dep.endswith(('.py', '.ts', '.js')):
                if not G.has_node(dep):
                    G.add_node(dep, type="file", file=dep, name=dep)
                target = dep

            if target and target != sym.name:
                target_type = G.nodes[target].get("type") if target in G else None
                if sym.type == "class" and target_type in ("class", "database_model"):
                    rel = "inherits"
                else:
                    rel = "depends_on"
                G.add_edge(sym.name, target, relationship=rel)
            elif dep in G and dep != sym.name:
                G.add_edge(sym.name, dep, relationship="depends_on")

        for call in sym.calls:
            target = call if call in G else name_lookup.get(call)
            if target and target != sym.name:
                G.add_edge(sym.name, target, relationship="calls")

    return G
