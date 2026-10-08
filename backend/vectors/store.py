import numpy as np
from sqlalchemy.orm import Session
from .models import SymbolEmbedding
from indexing.models import SymbolRecord
from typing import List, Tuple
from .embedder import generate_embedding

def store_embedding(db: Session, symbol_id: int, embedding: List[float]):
    record = SymbolEmbedding(symbol_id=symbol_id, embedding=embedding)
    db.add(record)
    db.commit()

def store_embeddings(db: Session, symbol_ids: List[int], embeddings: List[List[float]]):
    records = [
        SymbolEmbedding(symbol_id=sid, embedding=emb) 
        for sid, emb in zip(symbol_ids, embeddings)
    ]
    db.add_all(records)
    db.commit()

def search_similar_symbols(db: Session, query: str, top_k: int = 3) -> List[Tuple[SymbolRecord, float]]:
    query_emb = generate_embedding(query)
    query_vec = np.array(query_emb)
    
    all_embeddings = db.query(SymbolEmbedding).all()
    if not all_embeddings:
        return []
        
    scores = []
    for emb_rec in all_embeddings:
        target_vec = np.array(emb_rec.embedding)
        norm_q = np.linalg.norm(query_vec)
        norm_t = np.linalg.norm(target_vec)
        
        if norm_q == 0 or norm_t == 0:
            score = 0.0
        else:
            score = np.dot(query_vec, target_vec) / (norm_q * norm_t)
            
        scores.append((emb_rec.symbol_id, score))
        
    scores.sort(key=lambda x: x[1], reverse=True)
    
    top_results = []
    for symbol_id, score in scores[:top_k]:
        symbol = db.query(SymbolRecord).filter(SymbolRecord.id == symbol_id).first()
        if symbol:
            top_results.append((symbol, float(score)))
            
    return top_results
