from sqlalchemy import Column, Integer, JSON, ForeignKey
from indexing.models import Base

class SymbolEmbedding(Base):
    __tablename__ = 'symbol_embeddings'
    
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey('symbols.id', ondelete='CASCADE'), index=True)
    embedding = Column(JSON)
