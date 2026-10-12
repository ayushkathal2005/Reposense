import re
from typing import List, Dict, Any, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_
import networkx as nx

from indexing.models import SymbolRecord
from vectors.store import search_similar_symbols
from graph.queries import get_dependencies, get_callers

STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "with", "by",
    "is", "are", "was", "were", "what", "where", "how", "why", "when", "who",
    "which", "can", "could", "should", "does", "do", "did", "this", "that"
}

class ContextBuilder:
    def __init__(self, db: Session, graph: nx.DiGraph, repo_id: str = None, max_token_budget: int = 4000):
        self.db = db
        self.graph = graph if graph is not None else nx.DiGraph()
        self.repo_id = repo_id
        self.max_token_budget = max_token_budget

    def _extract_query_tokens(self, query: str) -> List[str]:
        tokens = re.findall(r'[a-zA-Z0-9_\.]+', query.lower())
        return [t for t in tokens if len(t) >= 2 and t not in STOP_WORDS]

    def select_primary_symbols(self, query: str, top_k: int = 5) -> List[Tuple[SymbolRecord, Dict[str, float]]]:
        """
        Retrieves candidates across semantic search, exact symbol match,
        filename/path match, and keyword search.
        Returns list of (SymbolRecord, score_dict).
        """
        candidate_map: Dict[int, Tuple[SymbolRecord, Dict[str, float]]] = {}

        # 1. Semantic Search (Dense)
        try:
            vector_results = search_similar_symbols(self.db, query, top_k=top_k, repo_id=self.repo_id)
            for sym, sim_score in vector_results:
                candidate_map[sym.id] = (sym, {
                    "semantic_score": max(0.0, float(sim_score)),
                    "exact_symbol_score": 0.0,
                    "path_match_score": 0.0,
                    "keyword_score": 0.0,
                    "graph_relevance_score": 0.0
                })
        except Exception:
            pass

        # 2. Exact Symbol and Keyword/Path Search (Sparse/Lexical)
        tokens = self._extract_query_tokens(query)
        if self.db and tokens:
            filters = []
            for token in tokens:
                filters.append(SymbolRecord.name.ilike(f"%{token}%"))
                filters.append(SymbolRecord.file_path.ilike(f"%{token}%"))
                filters.append(SymbolRecord.docstring.ilike(f"%{token}%"))

            q = self.db.query(SymbolRecord)
            if self.repo_id:
                q = q.filter(SymbolRecord.repository_name == self.repo_id)
            keyword_records = q.filter(or_(*filters)).limit(top_k * 3).all()

            for sym in keyword_records:
                sym_name_lower = (sym.name or "").lower()
                sym_file_lower = (sym.file_path or "").lower()
                doc_lower = (sym.docstring or "").lower()

                # Exact or near-exact symbol match
                exact_score = 0.0
                for token in tokens:
                    if sym_name_lower == token or sym_name_lower.split('.')[-1] == token:
                        exact_score = max(exact_score, 1.0)
                    elif token in sym_name_lower:
                        exact_score = max(exact_score, 0.5)

                # Path / filename match
                path_score = 0.0
                for token in tokens:
                    if token in sym_file_lower:
                        file_name = sym_file_lower.split('/')[-1].split('\\')[-1]
                        if token == file_name:
                            path_score = max(path_score, 1.0)
                        else:
                            path_score = max(path_score, 0.5)

                # Keyword match ratio
                matched_tokens = sum(1 for token in tokens if (token in sym_name_lower or token in sym_file_lower or token in doc_lower))
                kw_score = matched_tokens / len(tokens) if tokens else 0.0

                if sym.id in candidate_map:
                    existing_sym, scores = candidate_map[sym.id]
                    scores["exact_symbol_score"] = max(scores.get("exact_symbol_score", 0.0), exact_score)
                    scores["path_match_score"] = max(scores.get("path_match_score", 0.0), path_score)
                    scores["keyword_score"] = max(scores.get("keyword_score", 0.0), kw_score)
                else:
                    candidate_map[sym.id] = (sym, {
                        "semantic_score": 0.0,
                        "exact_symbol_score": exact_score,
                        "path_match_score": path_score,
                        "keyword_score": kw_score,
                        "graph_relevance_score": 0.0
                    })

        return list(candidate_map.values())

    def deduplicate(self, candidates: List[Tuple[SymbolRecord, Dict[str, float]]]) -> List[Tuple[SymbolRecord, Dict[str, float]]]:
        """Ensures each symbol appears at most once by symbol ID or unique file/name identity."""
        seen_ids = set()
        seen_identities = set()
        deduped = []
        for sym, scores in candidates:
            identity = (sym.name, sym.file_path, sym.start_line)
            if sym.id not in seen_ids and identity not in seen_identities:
                seen_ids.add(sym.id)
                seen_identities.add(identity)
                deduped.append((sym, scores))
        return deduped

    def expand_graph_context(self, candidates: List[SymbolRecord]) -> Set[str]:
        """Expands graph context for primary candidate symbols without unbounded graph bloat."""
        related_nodes = set()
        if not self.graph:
            return related_nodes

        for sym in candidates:
            sym_name = sym.name
            if sym_name and sym_name in self.graph:
                callers = get_callers(self.graph, sym_name)
                deps = get_dependencies(self.graph, sym_name)
                calls = [v for u, v, data in self.graph.out_edges(sym_name, data=True) if data.get('relationship') == 'calls']
                related_nodes.update(callers[:5])
                related_nodes.update(deps[:5])
                related_nodes.update(calls[:5])
        return related_nodes

    def rank_evidence(self, candidates: List[Tuple[SymbolRecord, Dict[str, float]]], related_nodes: Set[str], top_n: int = 10) -> List[SymbolRecord]:
        """
        Deterministic, explainable ranking formula:
        final_score = 0.35 * semantic + 0.30 * exact_symbol + 0.15 * path_match + 0.15 * keyword + 0.05 * graph_bonus
        """
        scored_symbols = []
        for sym, scores in candidates:
            graph_bonus = 0.0
            if sym.name and (sym.name in related_nodes or (self.graph and sym.name in self.graph)):
                graph_bonus = 1.0

            final_score = (
                0.35 * scores.get("semantic_score", 0.0)
                + 0.30 * scores.get("exact_symbol_score", 0.0)
                + 0.15 * scores.get("path_match_score", 0.0)
                + 0.15 * scores.get("keyword_score", 0.0)
                + 0.05 * graph_bonus
            )
            scored_symbols.append((sym, final_score))

        scored_symbols.sort(key=lambda x: x[1], reverse=True)
        return [sym for sym, _ in scored_symbols[:top_n]]

    def enforce_context_budget(self, ranked_symbols: List[SymbolRecord], related_nodes: Set[str], max_chars: int = 12000) -> Tuple[List[SymbolRecord], List[str]]:
        """Ensures the evidence fits within the allocated context budget."""
        budget_symbols = []
        used_chars = 0

        for sym in ranked_symbols:
            doc_len = len(sym.docstring or "")
            entry_len = len(sym.name or "") + len(sym.file_path or "") + 100 + min(doc_len, 500)
            if used_chars + entry_len > max_chars:
                break
            budget_symbols.append(sym)
            used_chars += entry_len

        budget_related = list(related_nodes)[:15]
        return budget_symbols, budget_related

    def build_llm_context(self, query: str, ranked_symbols: List[SymbolRecord], related_nodes: List[str]) -> str:
        prompt = (
            "SYSTEM INSTRUCTION: You are RepoSense's repository analysis engine.\n\n"
            "Answer only using repository evidence supplied in the context below.\n\n"
            "Never invent files, symbols, dependencies, APIs, execution paths, database operations, or architecture.\n"
            "For every important repository-specific claim, provide a source reference (file path and line numbers).\n\n"
            "If evidence is insufficient:\n"
            "- State clearly that you cannot establish this from the indexed repository.\n"
            "- Explain what evidence was found and what is missing.\n"
            "- Do not speculate or use intuition to guess repository details.\n\n"
        )
        prompt += f"User Query: {query}\n\n"
        prompt += "Primary Context (Code & Files):\n"

        for sym in ranked_symbols:
            prompt += f"- {sym.name} (File: {sym.file_path}, Type: {sym.type}, Lines: {sym.start_line}-{sym.end_line})\n"
            if sym.docstring:
                prompt += f"  Content/Docstring: {sym.docstring}\n"

        prompt += "\nRelated Structural Components (from Knowledge Graph):\n"
        for node in related_nodes:
            prompt += f"- {node}\n"

        prompt += "\nPlease provide a synthesized answer based ONLY on the context above."
        return prompt

    def get_context(self, query: str) -> Dict[str, Any]:
        candidates = self.select_primary_symbols(query)
        deduped = self.deduplicate(candidates)
        primary_symbols = [sym for sym, _ in deduped]
        related_nodes = self.expand_graph_context(primary_symbols)
        ranked = self.rank_evidence(deduped, related_nodes)
        budgeted_symbols, budgeted_nodes = self.enforce_context_budget(ranked, related_nodes)
        prompt = self.build_llm_context(query, budgeted_symbols, budgeted_nodes)

        sources = [
            {
                "name": sym.name,
                "file": sym.file_path,
                "file_path": sym.file_path,
                "lines": f"{sym.start_line}-{sym.end_line}"
            }
            for sym in budgeted_symbols
        ]

        return {
            "prompt": prompt,
            "sources": sources
        }
