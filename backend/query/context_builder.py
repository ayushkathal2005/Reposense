from typing import List, Dict, Any, Set
from sqlalchemy.orm import Session
from sqlalchemy import or_
import networkx as nx

from indexing.models import SymbolRecord
from vectors.store import search_similar_symbols
from graph.queries import get_dependencies, get_callers

class ContextBuilder:
    def __init__(self, db: Session, graph: nx.DiGraph, repo_id: str):
        self.db = db
        self.graph = graph
        self.repo_id = repo_id

    def select_primary_symbols(self, query: str, top_k: int = 5) -> List[SymbolRecord]:
        # 1. Semantic Search (Dense)
        vector_results = search_similar_symbols(self.db, query, top_k=top_k, repo_id=self.repo_id)
        semantic_symbols = [res[0] for res in vector_results]
        
        # 2. Keyword/Exact Match Search (Sparse/Metadata)
        query_terms = query.lower().split()
        keyword_symbols = []
        if query_terms:
            filters = []
            for term in query_terms:
                if len(term) > 3:  # Only search meaningful terms
                    filters.append(SymbolRecord.name.ilike(f"%{term}%"))
                    filters.append(SymbolRecord.file_path.ilike(f"%{term}%"))
            
            if filters and self.db:
                keyword_query = self.db.query(SymbolRecord).filter(
                    SymbolRecord.repository_name == self.repo_id,
                    or_(*filters)
                ).limit(top_k).all()
                keyword_symbols.extend(keyword_query)
                
        # Combine and Deduplicate
        all_symbols = semantic_symbols + keyword_symbols
        seen_ids = set()
        candidates = []
        for sym in all_symbols:
            if sym.id not in seen_ids:
                seen_ids.add(sym.id)
                candidates.append(sym)
                
        return candidates

    def expand_graph_context(self, primary_symbols: List[SymbolRecord]) -> Set[str]:
        related_nodes = set()
        for sym in primary_symbols:
            if sym.name in self.graph:
                callers = get_callers(self.graph, sym.name)
                deps = get_dependencies(self.graph, sym.name)
                calls = [v for u, v, data in self.graph.out_edges(sym.name, data=True) if data.get('relationship') == 'calls']
                related_nodes.update(callers)
                related_nodes.update(deps)
                related_nodes.update(calls)
        return related_nodes

    def rank_evidence(self, candidates: List[SymbolRecord], related_nodes: Set[str], top_n: int = 10) -> List[SymbolRecord]:
        # Simple heuristic ranking (placeholder for actual ranking logic)
        return candidates[:top_n]

    def build_llm_context(self, query: str, ranked_symbols: List[SymbolRecord], related_nodes: Set[str]) -> str:
        prompt = (
            "SYSTEM INSTRUCTION: You are a helpful software engineering and codebase analysis assistant. "
            "You will be provided with context retrieved from a repository. Use this context to answer the user's question. "
            "If the provided context does not fully contain the exact answer, use your general knowledge and intuition to deduce a reasonable answer based on standard tech stacks, file names, or common practices. "
            "Do not refuse to answer; provide the best possible educated guess and indicate that it is inferred.\n\n"
        )
        prompt += f"User Query: {query}\n\n"
        prompt += "Primary Context (Code & Files):\n"
        
        for sym in ranked_symbols:
            prompt += f"- {sym.name} (File: {sym.file_path}, Type: {sym.type}, Lines: {sym.start_line}-{sym.end_line})\n"
            if sym.docstring:
                prompt += f"  Content/Docstring: {sym.docstring}\n"
            
        prompt += "\nRelated Structural Components (from Knowledge Graph):\n"
        for node in list(related_nodes)[:15]:  # Limit related nodes to avoid token bloat
            prompt += f"- {node}\n"
            
        prompt += "\nPlease provide a synthesized answer based ONLY on the context above."
        return prompt

    def get_context(self, query: str) -> Dict[str, Any]:
        candidates = self.select_primary_symbols(query)
        related_nodes = self.expand_graph_context(candidates)
        ranked_symbols = self.rank_evidence(candidates, related_nodes)
        
        prompt = self.build_llm_context(query, ranked_symbols, related_nodes)
        
        sources = [
            {"name": sym.name, "file": sym.file_path, "lines": f"{sym.start_line}-{sym.end_line}"}
            for sym in ranked_symbols
        ]
        
        return {
            "prompt": prompt,
            "sources": sources
        }
