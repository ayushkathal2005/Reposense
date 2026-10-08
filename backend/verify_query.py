import json
from indexing.database import init_db, SessionLocal, engine
from indexing.service import index_symbols
from indexing.models import Base, SymbolRecord
from vectors.store import store_embedding
from vectors.embedder import generate_embedding
from parsers.models import Symbol
from graph import build_knowledge_graph
from query.engine import QueryEngine

def setup_db():
    Base.metadata.create_all(bind=engine)

def main():
    setup_db()
    db = SessionLocal()
    
    symbols = []
    
    symbols.append(Symbol(
        type="function", name="login", file="auth.py", start_line=10, end_line=15, 
        docstring="Handles user authentication by verifying credentials against the database.",
        calls=["verify_user"]
    ))
    symbols.append(Symbol(
        type="function", name="verify_user", file="db.py", start_line=20, end_line=30, 
        docstring="Queries the database to check if the password hash matches for the given email."
    ))
    symbols.append(Symbol(
        type="class", name="SessionManager", file="auth.py", start_line=40, end_line=50, 
        docstring="Manages active user sessions after a successful login.",
        dependencies=["db.py"]
    ))
    
    db.query(SymbolRecord).delete() 
    from vectors.models import SymbolEmbedding
    db.query(SymbolEmbedding).delete()
    db.commit()
    
    index_symbols(db, "test_repo", symbols, "Python")
    
    records = db.query(SymbolRecord).all()
    for record in records:
        text_to_embed = f"{record.name}: {record.docstring or ''}"
        emb = generate_embedding(text_to_embed)
        store_embedding(db, record.id, emb)
        
    graph = build_knowledge_graph(symbols)
    
    engine_obj = QueryEngine(db, graph)
    
    query = "How does login work?"
    print(f"\\n--- Query: '{query}' ---")
    
    result = engine_obj.query(query, top_k=2)
    
    print("\\nSynthesized Answer:")
    print(result["answer"])
    
    print("\\nSources Used:")
    for src in result["sources"]:
        print(f" - {src['name']} ({src['file']}:{src['lines']})")
        
    print("\\nGenerated Prompt:")
    print(result["prompt"])

if __name__ == "__main__":
    main()
