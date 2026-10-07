import subprocess
import urllib.parse
from pathlib import Path

class GitClientError(Exception):
    pass

def validate_github_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if parsed.netloc != "github.com":
            return False
        parts = parsed.path.strip("/").split("/")
        if len(parts) != 2:
            return False
        return True
    except Exception:
        return False

def clone_repository(url: str, target_dir: Path) -> None:
    if not validate_github_url(url):
        raise GitClientError(f"Invalid GitHub URL: {url}")
    
    try:
        # Clone only the latest commit to save time and space
        subprocess.run(
            ["git", "clone", "--depth", "1", url, str(target_dir)],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise GitClientError(f"Failed to clone repository: {e.stderr}")
