from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.orm import declarative_base

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
