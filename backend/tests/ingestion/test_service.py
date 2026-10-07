import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from ingestion.service import ingest_repository
from ingestion.git_client import GitClientError

@patch('ingestion.service.clone_repository')
@patch('ingestion.service.ingest_directory')
def test_ingest_repository_success(mock_ingest, mock_clone, tmp_path):
    mock_ingest.return_value = "metadata"
    
    result = ingest_repository("https://github.com/user/repo", tmp_path)
    
    mock_clone.assert_called_once()
    assert result == "metadata"

def test_ingest_repository_invalid_url(tmp_path):
    with pytest.raises(GitClientError):
        ingest_repository("invalid_url", tmp_path)
