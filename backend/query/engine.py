import networkx as nx
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from vectors.store import search_similar_symbols
from graph.queries import get_dependencies, get_callers
from indexing.models import SymbolRecord
from .llm import LLMClient

class QueryEngine:
    def __init__(self, db: Session, graph: nx.DiGraph, llm: LLMClient = None):
        self.db = db
        self.graph = graph
        self.llm = llm or LLMClient()
        
    def _compile_prompt(self, query: str, primary_symbols: List[SymbolRecord], related_nodes: List[str]) -> str:
        prompt = f"User Query: {query}\\n\\n"
        prompt += "Primary Context:\\n"
        for sym in primary_symbols:
            prompt += f"- {sym.name} (File: {sym.file_path}, Lines: {sym.start_line}-{sym.end_line})\\n"
            prompt += f"  Docstring: {sym.docstring}\\n"
            
        prompt += "\\nRelated Components (from Knowledge Graph):\\n"
        for node in related_nodes:
            prompt += f"- {node}\\n"
            
        prompt += "\\nPlease provide a synthesized answer based on the context above."
        return prompt

    def query(self, text: str, top_k: int = 3) -> Dict[str, Any]:
        # 1. Semantic Search
        vector_results = search_similar_symbols(self.db, text, top_k=top_k)
        primary_symbols = [res[0] for res in vector_results]
        
        # 2. Knowledge Graph Expansion
        related_nodes = set()
        for sym in primary_symbols:
            if sym.name in self.graph:
                callers = get_callers(self.graph, sym.name)
                deps = get_dependencies(self.graph, sym.name)
                calls = [v for u, v, data in self.graph.out_edges(sym.name, data=True) if data.get('relationship') == 'calls']
                related_nodes.update(callers)
                related_nodes.update(deps)
                related_nodes.update(calls)
            
        # 3. Prompt Compilation
        prompt = self._compile_prompt(text, primary_symbols, list(related_nodes))
        
        # 4. LLM Synthesize
        answer = self.llm.generate(prompt)
        
        # 5. Return result with sources
        sources = [
            {"name": sym.name, "file": sym.file_path, "lines": f"{sym.start_line}-{sym.end_line}"}
            for sym in primary_symbols
        ]
        
        return {
            "answer": answer,
            "sources": sources,
            "prompt": prompt
        }
