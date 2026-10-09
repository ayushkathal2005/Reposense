from typing import List, Dict, Any
from sqlalchemy.orm import Session
import networkx as nx
from indexing.models import SymbolRecord
from .llm import LLMClient
from .context_builder import ContextBuilder

class QueryEngine:
    def __init__(self, db: Session, graph: nx.DiGraph, llm: LLMClient = None, repo_id: str = None):
        self.db = db
        self.graph = graph
        self.llm = llm or LLMClient()
        self.repo_id = repo_id
        
    def query(self, text: str, top_k: int = 3) -> Dict[str, Any]:
        builder = ContextBuilder(self.db, self.graph, self.repo_id)
        
        # 1. Build context via hybrid retrieval
        context_data = builder.get_context(text)
        
        # 2. LLM Synthesize
        answer = self.llm.generate(context_data["prompt"])
        
        return {
            "answer": answer,
            "sources": context_data["sources"],
            "prompt": context_data["prompt"]
        }
