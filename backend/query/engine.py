from typing import List, Dict, Any
from sqlalchemy.orm import Session
import networkx as nx
from indexing.models import SymbolRecord
from .llm import LLMClient
from .context_builder import ContextBuilder
from schemas.models import AnalysisResponse, EvidenceItem

class QueryEngine:
    def __init__(self, db: Session, graph: nx.DiGraph, llm: LLMClient = None, repo_id: str = None):
        self.db = db
        self.graph = graph
        self.llm = llm or LLMClient()
        self.repo_id = repo_id

    def query(self, text: str, top_k: int = 3) -> AnalysisResponse:
        builder = ContextBuilder(self.db, self.graph, self.repo_id)

        # 1. Build context via hybrid retrieval
        context_data = builder.get_context(text)
        sources = context_data.get("sources", [])

        # 2. LLM Synthesize
        prompt = context_data["prompt"]
        answer = self.llm.generate(prompt)

        # 3. Structure evidence and references
        evidence_items: List[EvidenceItem] = []
        source_refs: List[str] = []
        related_syms: List[str] = []

        for s in sources:
            sym_name = s.get("name")
            f_path = s.get("file") or s.get("file_path", "")
            lines = s.get("lines")
            start_line = None
            if lines:
                try:
                    start_line = int(str(lines).split("-")[0])
                except Exception:
                    pass

            evidence_items.append(
                EvidenceItem(
                    file=f_path,
                    line=start_line,
                    symbol=sym_name
                )
            )
            if sym_name:
                related_syms.append(sym_name)
            if f_path:
                ref = f"{f_path}:{lines}" if lines else f_path
                source_refs.append(ref)

        warnings: List[str] = []
        confidence = "high"
        if not sources:
            confidence = "low"
            warnings.append("No direct evidence found in repository index matching query.")
        elif "cannot establish" in answer.lower():
            confidence = "medium"
            warnings.append("Indexed evidence was insufficient for complete answer.")

        return AnalysisResponse(
            answer=answer,
            confidence=confidence,
            evidence=evidence_items,
            related_symbols=related_syms,
            source_references=source_refs,
            warnings=warnings,
            unresolved=[],
            sources=sources,
            prompt=prompt
        )

