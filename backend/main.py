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
from query.llm import LLMClient
from tracing import ExecutionTracer, TraceRequest
from architecture import ArchitectureAnalyzer
from impact import ChangeImpactAnalyzer, ImpactRequest
from debugging import RepoDebugger, DebugRequest
from documentation import RepoDocGenerator, DocRequest
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
            "dist", "build", "coverage", ".next", ".idea", ".vscode"
        }
        secret_file_patterns = {
            ".env", ".env.local", ".env.production", ".env.development",
            "id_rsa", "id_ecdsa", "id_ed25519", "credentials.json",
            "service_account.json"
        }
        secret_extensions = {".pem", ".key", ".p12", ".pfx"}
        supported_exts = {".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts"}

        MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB cap per source file

        for file_path in repo_path.rglob("*"):
            if not file_path.is_file():
                continue

            # 1. Security: Path Traversal check
            try:
                resolved_file = file_path.resolve()
                if not resolved_file.is_relative_to(repo_path.resolve()):
                    continue
            except Exception:
                continue

            # 2. Security: Ignore secret and credential files
            fname_lower = file_path.name.lower()
            if (
                fname_lower in secret_file_patterns
                or fname_lower.startswith(".env.")
                or file_path.suffix.lower() in secret_extensions
            ):
                continue

            # 3. Security: Enforce single-file size ceiling
            try:
                if file_path.stat().st_size > MAX_FILE_SIZE:
                    continue
            except Exception:
                continue

            # 4. Check directory filters
            if any(part in ignored_dirs for part in file_path.parts):
                continue

            # 5. Safe Parsing with per-file fault tolerance
            if file_path.suffix.lower() in supported_exts:
                try:
                    rel_path = str(file_path.relative_to(repo_path)).replace("\\", "/")
                    file_symbols = parse_file(file_path, rel_path)
                    symbols.extend(file_symbols)
                except Exception as parse_err:
                    print(f"Warning: Failed to parse {file_path.name}: {parse_err}")

        # Index generic important files for context (with safe size limit)
        for target_file in ["package.json", "README.md", "requirements.txt", "pom.xml", "build.gradle"]:
            file_path = repo_path / target_file
            if file_path.exists():
                try:
                    if file_path.stat().st_size <= MAX_FILE_SIZE:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
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
            try:
                text_to_embed = f"{record.name}: {record.docstring or ''}"
                emb = generate_embedding(text_to_embed)
                store_embedding(db, record.id, emb)
            except Exception as emb_err:
                print(f"Warning: Failed to embed symbol {record.name}: {emb_err}")

        # Build and persist knowledge graph during ingestion (handles empty symbols cleanly)
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

@app.get("/api/repos/{repo_id}/architecture")
def api_repo_architecture(repo_id: str):
    db = SessionLocal()
    try:
        graph = get_or_load_graph(db, repo_id)
        if not graph or len(graph.nodes) == 0:
            raise HTTPException(status_code=404, detail="Repository graph not found or empty")
        analyzer = ArchitectureAnalyzer(graph)
        return analyzer.analyze()
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


@app.post("/api/trace")
def api_trace(req: TraceRequest):
    if req.repo_id in ingestion_status and ingestion_status[req.repo_id] == "processing":
        raise HTTPException(status_code=400, detail="Repo ingestion still in progress")

    db = SessionLocal()
    try:
        graph = get_or_load_graph(db, req.repo_id)
        if not graph or len(graph.nodes) == 0:
            raise HTTPException(status_code=404, detail="Repository graph not found or empty")
        llm = LLMClient()
        tracer = ExecutionTracer(graph, llm=llm)
        query_val = req.entrypoint or req.query or ""
        trace_result = tracer.trace(query_val, target_symbol=req.target, max_depth=req.max_depth)
        return trace_result
    finally:
        db.close()


@app.post("/api/impact")
def api_impact(req: ImpactRequest):
    if req.repo_id in ingestion_status and ingestion_status[req.repo_id] == "processing":
        raise HTTPException(status_code=400, detail="Repo ingestion still in progress")

    db = SessionLocal()
    try:
        graph = get_or_load_graph(db, req.repo_id)
        if not graph or len(graph.nodes) == 0:
            raise HTTPException(status_code=404, detail="Repository graph not found or empty")

        llm = LLMClient()
        analyzer = ChangeImpactAnalyzer(graph, llm=llm)
        result = analyzer.analyze(
            symbol_query=req.symbol,
            file_path=req.file_path,
            max_depth=req.max_depth
        )
        return result
    finally:
        db.close()


@app.post("/api/debug")
def api_debug(req: DebugRequest):
    if req.repo_id in ingestion_status and ingestion_status[req.repo_id] == "processing":
        raise HTTPException(status_code=400, detail="Repo ingestion still in progress")

    db = SessionLocal()
    try:
        graph = get_or_load_graph(db, req.repo_id)
        if not graph or len(graph.nodes) == 0:
            raise HTTPException(status_code=404, detail="Repository graph not found or empty")

        base_dir = Path.cwd() / "data" / "repos"
        repo_path = None
        for child in base_dir.glob("*"):
            if child.is_dir():
                repo_path = child
                break

        llm = LLMClient()
        debugger = RepoDebugger(graph, base_repo_path=repo_path, llm=llm)
        result = debugger.analyze(req)
        return result
    finally:
        db.close()


@app.post("/api/documentation")
def api_documentation(req: DocRequest):
    if req.repo_id in ingestion_status and ingestion_status[req.repo_id] == "processing":
        raise HTTPException(status_code=400, detail="Repo ingestion still in progress")

    db = SessionLocal()
    try:
        graph = get_or_load_graph(db, req.repo_id)
        if not graph or len(graph.nodes) == 0:
            raise HTTPException(status_code=404, detail="Repository graph not found or empty")

        base_dir = Path.cwd() / "data" / "repos"
        repo_path = None
        for child in base_dir.glob("*"):
            if child.is_dir():
                repo_path = child
                break

        llm = LLMClient()
        generator = RepoDocGenerator(graph, base_repo_path=repo_path, llm=llm)
        result = generator.generate(req)
        return result
    finally:
        db.close()

