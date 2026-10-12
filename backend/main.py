import uuid
from typing import Dict
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
load_dotenv(Path(__file__).parent.parent / ".env")

from ingestion.git_client import GitClientError
from ingestion.service import ingest_repository
from parsers import parse_file
from indexing.database import engine, SessionLocal
from indexing.models import Base, SymbolRecord
from indexing.service import index_symbols
from vectors.embedder import generate_embedding
from vectors.store import store_embedding
from graph import build_knowledge_graph, save_graph, load_graph, get_or_load_graph, inspect_graph
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
        ignored_dirs = {
            ".git", "node_modules", "venv", ".venv", "__pycache__",
            "dist", "build", "coverage", ".next"
        }
        supported_exts = {".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts"}

        for file_path in repo_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in supported_exts:
                if not any(part in ignored_dirs for part in file_path.parts):
                    rel_path = str(file_path.relative_to(repo_path)).replace("\\", "/")
                    file_symbols = parse_file(file_path, rel_path)
                    symbols.extend(file_symbols)
                
        # Index generic important files for context
        for target_file in ["package.json", "README.md", "requirements.txt", "pom.xml", "build.gradle"]:
            file_path = repo_path / target_file
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding="utf-8")
                    # Truncate content if it's too long
                    if len(content) > 2000:
                        content = content[:2000] + "..."
                    sym = Symbol(
                        type="file",
                        name=target_file,
                        file=target_file,
                        language="Config",
                        start_line=1,
                        end_line=content.count('\n') + 1,
                        calls=[],
                        dependencies=[],
                        docstring=content,
                        decorators=[]
                    )
                    symbols.append(sym)
                except Exception:
                    pass
                
        index_symbols(db, repo_id, symbols)
        
        records = db.query(SymbolRecord).filter(SymbolRecord.repository_name == repo_id).all()
        for record in records:
            text_to_embed = f"{record.name}: {record.docstring or ''}"
            emb = generate_embedding(text_to_embed)
            store_embedding(db, record.id, emb)
            
        # Build and persist knowledge graph during ingestion
        graph = build_knowledge_graph(symbols, repo_id=repo_id)
        save_graph(db, repo_id, graph)

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

@app.get("/api/repos/{repo_id}/graph")
def api_repo_graph(repo_id: str):
    db = SessionLocal()
    try:
        graph = load_graph(db, repo_id)
        if not graph:
            raise HTTPException(status_code=404, detail="Graph not found for repository")
        return inspect_graph(graph)
    finally:
        db.close()

@app.post("/api/query")
def api_query(req: QueryRequest):
    if req.repo_id not in ingestion_status or ingestion_status[req.repo_id] != "completed":
        raise HTTPException(status_code=400, detail="Repo not found or not fully ingested")
        
    db = SessionLocal()
    try:
        # Retrieve persistent knowledge graph directly without rebuilding
        graph = get_or_load_graph(db, req.repo_id)
        engine_obj = QueryEngine(db, graph, repo_id=req.repo_id)
        
        result = engine_obj.query(req.query)
        return result
    finally:
        db.close()

