from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch
from ingestion.models import RepositoryMetadata

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "RepoSense API is running"}

@patch('main.ingest_repository')
def test_ingest_repo_success(mock_ingest):
    mock_metadata = RepositoryMetadata(
        url="https://github.com/user/repo",
        name="repo",
        total_files=0,
        languages_detected=[],
        files=[]
    )
    mock_ingest.return_value = mock_metadata
    
    response = client.post("/ingest", json={"url": "https://github.com/user/repo"})
    assert response.status_code == 200
    assert response.json()["name"] == "repo"

@patch('main.ingest_repository')
def test_ingest_repo_error(mock_ingest):
    from ingestion.git_client import GitClientError
    mock_ingest.side_effect = GitClientError("Invalid GitHub URL")
    
    response = client.post("/ingest", json={"url": "invalid_url"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid GitHub URL"
