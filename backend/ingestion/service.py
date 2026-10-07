import shutil
import urllib.parse
from pathlib import Path
from .git_client import clone_repository, validate_github_url, GitClientError
from .detector import ingest_directory
from .models import RepositoryMetadata

def ingest_repository(url: str, base_dir: Path) -> RepositoryMetadata:
    if not validate_github_url(url):
        raise GitClientError("Invalid GitHub URL")
        
    parsed = urllib.parse.urlparse(url)
    # Extracts "user/repo" -> "repo"
    parts = parsed.path.strip("/").split("/")
    repo_name = parts[1]
    
    workspace_dir = base_dir / repo_name
    
    if workspace_dir.exists():
        # Clean up existing directory for a fresh clone
        # In a real app we might just 'git pull' but a fresh clone is simpler and safer for ingestion
        import stat
        def remove_readonly(func, path, _):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        import os
        shutil.rmtree(workspace_dir, onerror=remove_readonly)
        
    clone_repository(url, workspace_dir)
    return ingest_directory(url, repo_name, workspace_dir)
