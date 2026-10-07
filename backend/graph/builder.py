import networkx as nx
from typing import List
from parsers.models import Symbol

def build_knowledge_graph(symbols: List[Symbol]) -> nx.DiGraph:
    G = nx.DiGraph()
    
    # First pass: add all nodes
    for sym in symbols:
        G.add_node(
            sym.name, 
            type=sym.type, 
            file=sym.file, 
            start_line=sym.start_line,
            end_line=sym.end_line
        )
        
        if not G.has_node(sym.file):
            G.add_node(sym.file, type="file", file=sym.file)
            
        G.add_edge(sym.name, sym.file, relationship="defined_in")
        
    # Second pass: add edges (Calls, Dependencies)
    name_lookup = {sym.name.split('.')[-1]: sym.name for sym in symbols}
    
    for sym in symbols:
        for dep in sym.dependencies:
            if dep in G:
                G.add_edge(sym.name, dep, relationship="depends_on")
            elif dep in name_lookup:
                G.add_edge(sym.name, name_lookup[dep], relationship="depends_on")
                
        for call in sym.calls:
            if call in G:
                G.add_edge(sym.name, call, relationship="calls")
            elif call in name_lookup:
                G.add_edge(sym.name, name_lookup[call], relationship="calls")
                
    return G
