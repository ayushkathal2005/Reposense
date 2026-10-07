import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from indexing.models import Base, SymbolRecord
from indexing.service import index_symbols, search_symbols
from parsers.models import Symbol

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_index_and_search_symbols(db_session):
    symbols = [
        Symbol(
            type="function",
            name="authenticate_user",
            file="auth.py",
            start_line=10,
            end_line=20,
            docstring="Authenticates a user with JWT."
        ),
        Symbol(
            type="class",
            name="DatabaseConnection",
            file="db.py",
            start_line=5,
            end_line=50,
            docstring="Handles PostgreSQL connection."
        ),
        Symbol(
            type="method",
            name="OrderService.process_payment",
            file="order.py",
            start_line=30,
            end_line=45,
            docstring="Processes a payment for an order."
        )
    ]
    
    index_symbols(db_session, "test_repo", symbols, "Python")
    
    # Exact search
    results = search_symbols(db_session, "authenticate_user", exact=True)
    assert len(results) == 1
    assert results[0].name == "authenticate_user"
    
    # Partial search on docstring
    results = search_symbols(db_session, "JWT", exact=False)
    assert len(results) == 1
    assert results[0].name == "authenticate_user"
    
    # Partial search on name (case insensitive)
    results = search_symbols(db_session, "payment", exact=False)
    assert len(results) == 1
    assert results[0].name == "OrderService.process_payment"
    
    # Partial search on path
    results = search_symbols(db_session, "db.py", exact=False)
    assert len(results) == 1
    assert results[0].name == "DatabaseConnection"

    # Filter by repo
    results = search_symbols(db_session, "auth", repository_name="wrong_repo", exact=False)
    assert len(results) == 0

def test_language_filtering(db_session):
    symbols = [
        Symbol(type="function", name="main", file="main.py", start_line=1, end_line=2)
    ]
    index_symbols(db_session, "test_repo", symbols, "Python")
    
    results = search_symbols(db_session, "main", language="JavaScript", exact=False)
    assert len(results) == 0
    
    results = search_symbols(db_session, "main", language="Python", exact=False)
    assert len(results) == 1
