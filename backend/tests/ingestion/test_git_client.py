import pytest
from pathlib import Path
from ingestion.git_client import validate_github_url, clone_repository, GitClientError

def test_validate_github_url():
    assert validate_github_url("https://github.com/user/repo") == True
    assert validate_github_url("http://github.com/user/repo") == True
    assert validate_github_url("https://github.com/user/repo/") == True
    
    # Invalid URLs
    assert validate_github_url("https://gitlab.com/user/repo") == False
    assert validate_github_url("https://github.com/user") == False
    assert validate_github_url("https://github.com/user/repo/extra") == False
    assert validate_github_url("not_a_url") == False

def test_clone_repository_invalid_url(tmp_path):
    with pytest.raises(GitClientError, match="Invalid GitHub URL"):
        clone_repository("https://gitlab.com/user/repo", tmp_path)
