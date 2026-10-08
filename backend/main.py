import uuid
from typing import Dict
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from pathlib import Path

from ingestion.git_client import GitClientError
from ingestion.service import ingest_repository
from parsers import parse_file
from indexing.database import engine, SessionLocal
from indexing.models import Base, SymbolRecord
from indexing.service import index_symbols
from vectors.embedder import generate_embedding
from vectors.store import store_embedding
from graph import build_knowledge_graph
from query.engine import QueryEngine
from parsers.models import Symbol
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title="RepoSense API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok"}

ingestion_status: Dict[str, str] = {}

class IngestRequest(BaseModel):
    url: str

class QueryRequest(BaseModel):
    repo_id: str
    query: str

def run_ingestion(repo_id: str, url: str):
    db = SessionLocal()
    try:
        base_dir = Path.cwd() / "data" / "repos"
        metadata = ingest_repository(url, base_dir)
        repo_path = base_dir / metadata.name
        
        symbols = []
        for py_file in repo_path.rglob("*.py"):
            if "venv" not in py_file.parts and "tests" not in py_file.parts:
                rel_path = str(py_file.relative_to(repo_path)).replace("\\", "/")
                file_symbols = parse_file(py_file, rel_path)
                symbols.extend(file_symbols)
                
        index_symbols(db, repo_id, symbols, "Python")
        
        records = db.query(SymbolRecord).filter(SymbolRecord.repository_name == repo_id).all()
        for record in records:
            text_to_embed = f"{record.name}: {record.docstring or ''}"
            emb = generate_embedding(text_to_embed)
            store_embedding(db, record.id, emb)
            
        ingestion_status[repo_id] = "completed"
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Ingestion failed for {repo_id}: {e}")
        ingestion_status[repo_id] = "failed"
    finally:
        db.close()


@app.post("/api/repos/ingest")
def api_ingest_repo(req: IngestRequest, background_tasks: BackgroundTasks):
    repo_id = str(uuid.uuid4())
    ingestion_status[repo_id] = "processing"
    background_tasks.add_task(run_ingestion, repo_id, req.url)
    return {"repo_id": repo_id, "status": "processing"}

@app.get("/api/repos/{repo_id}/status")
def api_repo_status(repo_id: str):
    if repo_id not in ingestion_status:
        raise HTTPException(status_code=404, detail="Repo ID not found")
    return {"repo_id": repo_id, "status": ingestion_status[repo_id]}

@app.post("/api/query")
def api_query(req: QueryRequest):
    if req.repo_id not in ingestion_status or ingestion_status[req.repo_id] != "completed":
        raise HTTPException(status_code=400, detail="Repo not found or not fully ingested")
        
    db = SessionLocal()
    try:
        records = db.query(SymbolRecord).filter(SymbolRecord.repository_name == req.repo_id).all()
        
        symbols = []
        for r in records:
            sym = Symbol(
                type=r.type,
                name=r.name,
                file=r.file_path,
                start_line=r.start_line,
                end_line=r.end_line,
                calls=r.calls or [],
                dependencies=r.dependencies or [],
                docstring=r.docstring,
                decorators=r.decorators or []
            )
            symbols.append(sym)
            
        graph = build_knowledge_graph(symbols)
        engine_obj = QueryEngine(db, graph, repo_id=req.repo_id)
        
        result = engine_obj.query(req.query)
        return result
    finally:
        db.close()

