from sqlalchemy.orm import Session
from sqlalchemy import or_
from .models import SymbolRecord
from typing import List, Optional
from parsers import Symbol

def index_symbols(db: Session, repository_name: str, symbols: List[Symbol], language: str):
    records = []
    for s in symbols:
        record = SymbolRecord(
            repository_name=repository_name,
            type=s.type,
            name=s.name,
            file_path=s.file,
            language=language,
            start_line=s.start_line,
            end_line=s.end_line,
            calls=s.calls,
            dependencies=s.dependencies,
            docstring=s.docstring,
            decorators=s.decorators
        )
        records.append(record)
    
    db.add_all(records)
    db.commit()

def search_symbols(db: Session, 
                   query: str, 
                   repository_name: Optional[str] = None,
                   exact: bool = False,
                   file_path: Optional[str] = None,
                   language: Optional[str] = None,
                   limit: int = 50) -> List[SymbolRecord]:
    
    q = db.query(SymbolRecord)
    
    if repository_name:
        q = q.filter(SymbolRecord.repository_name == repository_name)
        
    if file_path:
        q = q.filter(SymbolRecord.file_path == file_path)
        
    if language:
        q = q.filter(SymbolRecord.language == language)
        
    if exact:
        q = q.filter(SymbolRecord.name == query)
    else:
        # Partial search on name, docstring, or path
        search_term = f"%{query}%"
        q = q.filter(
            or_(
                SymbolRecord.name.ilike(search_term),
                SymbolRecord.docstring.ilike(search_term),
                SymbolRecord.file_path.ilike(search_term)
            )
        )
        
    return q.limit(limit).all()
