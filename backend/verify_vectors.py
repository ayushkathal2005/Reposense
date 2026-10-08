import json
from indexing.database import init_db, SessionLocal, engine
from indexing.service import index_symbols
from indexing.models import Base, SymbolRecord
from vectors.store import store_embedding, search_similar_symbols
from vectors.embedder import generate_embedding
from parsers.models import Symbol

def setup_db():
    Base.metadata.create_all(bind=engine)

def main():
    setup_db()
    db = SessionLocal()
    
    symbols = []
    
    target_symbols = [
        Symbol(type="method", name="process_payment", file="payments.py", start_line=1, end_line=5, docstring="Handles credit card charges and billing transactions."),
        Symbol(type="function", name="login", file="auth.py", start_line=10, end_line=15, docstring="Verifies user credentials and starts a session."),
        Symbol(type="class", name="DatabaseManager", file="db.py", start_line=1, end_line=50, docstring="Manages connections and transactions for the persistence layer."),
        Symbol(type="function", name="calculate_total", file="cart.py", start_line=5, end_line=10, docstring="Sums up the prices of items in the shopping cart."),
        Symbol(type="function", name="send_email", file="notifications.py", start_line=1, end_line=10, docstring="Delivers a message to a user's inbox.")
    ]
    
    symbols.extend(target_symbols)
    
    for i in range(5, 55):
        symbols.append(Symbol(
            type="function",
            name=f"dummy_function_{i}",
            file=f"dummy_{i%5}.py",
            start_line=1,
            end_line=5,
            docstring=f"This is a placeholder function number {i} that does basic generic things."
        ))
        
    db.query(SymbolRecord).delete() 
    from vectors.models import SymbolEmbedding
    db.query(SymbolEmbedding).delete()
    db.commit()
    
    index_symbols(db, "test_repo", symbols, "Python")
    
    records = db.query(SymbolRecord).all()
    print(f"Generating embeddings for {len(records)} symbols...")
    
    for record in records:
        text_to_embed = f"{record.name}: {record.docstring or ''}"
        emb = generate_embedding(text_to_embed)
        store_embedding(db, record.id, emb)
        
    print("Embeddings stored successfully!")
    
    query = "how is money handled"
    print(f"\\n--- Semantic Search Query: '{query}' ---")
    
    results = search_similar_symbols(db, query, top_k=3)
    for idx, (symbol, score) in enumerate(results):
        print(f"[{idx+1}] Score: {score:.4f} | {symbol.type.upper()}: {symbol.name} (File: {symbol.file_path})")
        print(f"    Docs: {symbol.docstring}\\n")

if __name__ == "__main__":
    main()
