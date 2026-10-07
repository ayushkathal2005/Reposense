import json
from indexing.database import init_db, SessionLocal, engine
from indexing.service import index_symbols, search_symbols
from parsers.models import Symbol

def reset_db():
    from indexing.models import Base
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def main():
    reset_db()
    db = SessionLocal()
    
    # 1. Insert mock symbols for testing requirements
    symbols = [
        Symbol(
            type="function",
            name="authenticate_user",
            file="auth/services.py",
            start_line=15,
            end_line=30,
            docstring="Handles authentication for a user and returns a JWT token."
        ),
        Symbol(
            type="class",
            name="DatabaseConnection",
            file="db/connection.py",
            start_line=5,
            end_line=50,
            docstring="Handles the primary database connection to PostgreSQL."
        ),
        Symbol(
            type="class",
            name="Order",
            file="orders/models.py",
            start_line=10,
            end_line=25,
            docstring="Represents an order in the system."
        ),
        Symbol(
            type="method",
            name="PaymentService.process_payment",
            file="payments/services.py",
            start_line=40,
            end_line=60,
            docstring="Processes a payment for an order using Stripe."
        ),
        Symbol(
            type="function",
            name="verify_jwt",
            file="auth/jwt.py",
            start_line=5,
            end_line=15,
            docstring="Verifies the authenticity of a JWT token."
        )
    ]
    
    index_symbols(db, "test_repo", symbols, "Python")
    
    # 2. Run test searches
    queries = ["authentication", "database", "order", "payment", "JWT"]
    
    for q in queries:
        print(f"\\n--- Search Query: '{q}' ---")
        results = search_symbols(db, q, exact=False)
        for idx, r in enumerate(results):
            # Sensible ranking logic isn't heavily implemented yet, but order is deterministic
            print(f"[{idx+1}] {r.type.upper()}: {r.name} (File: {r.file_path}, Lines: {r.start_line}-{r.end_line})")
            if r.docstring:
                print(f"    Docs: {r.docstring}")
            print()

if __name__ == "__main__":
    main()
