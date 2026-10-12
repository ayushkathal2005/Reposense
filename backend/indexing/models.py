from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class SymbolRecord(Base):
    __tablename__ = 'symbols'
    
    id = Column(Integer, primary_key=True, index=True)
    repository_name = Column(String, index=True)
    type = Column(String, index=True)
    name = Column(String, index=True)
    file_path = Column(String, index=True)
    language = Column(String, index=True)
    start_line = Column(Integer)
    end_line = Column(Integer)
    calls = Column(JSON)
    dependencies = Column(JSON)
    docstring = Column(String)
    decorators = Column(JSON)

class GraphRecord(Base):
    __tablename__ = 'repository_graphs'
    
    id = Column(Integer, primary_key=True, index=True)
    repository_name = Column(String, unique=True, index=True)
    graph_data = Column(JSON)
    node_count = Column(Integer, default=0)
    edge_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
