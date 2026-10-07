from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
from ingestion.service import ingest_repository
from ingestion.git_client import GitClientError

app = FastAPI(title="RepoSense API")

class IngestRequest(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {"message": "RepoSense API is running"}

@app.post("/ingest")
def ingest_repo(req: IngestRequest):
    base_dir = Path.cwd() / "data" / "repos"
    try:
        metadata = ingest_repository(req.url, base_dir)
        return metadata
    except GitClientError as e:
        raise HTTPException(status_code=400, detail=str(e))
