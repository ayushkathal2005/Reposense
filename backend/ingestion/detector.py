import os
from pathlib import Path
from .models import RepositoryMetadata, FileInfo

IGNORED_DIRS = {
    ".git", "node_modules", "venv", ".venv", 
    "__pycache__", "dist", "build", "coverage"
}
IGNORED_FILES = {
    ".env", ".env.local", ".env.development", 
    ".env.test", ".env.production"
}

LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript"
}

def detect_language(path: Path) -> str | None:
    ext = path.suffix.lower()
    return LANGUAGE_MAP.get(ext)

def ingest_directory(repo_url: str, repo_name: str, root_dir: Path) -> RepositoryMetadata:
    files = []
    languages = set()
    
    for current_root, dirs, filenames in os.walk(root_dir):
        # Prevent traversal into ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        
        current_root_path = Path(current_root)
        
        for name in filenames:
            if name in IGNORED_FILES or name in IGNORED_DIRS:
                continue
            
            file_path = current_root_path / name
            rel_path = str(file_path.relative_to(root_dir)).replace("\\", "/")
            
            lang = detect_language(file_path)
            if lang:
                languages.add(lang)
            
            try:
                size = file_path.stat().st_size
                files.append(FileInfo(path=rel_path, language=lang, size=size))
            except Exception:
                pass
                
    return RepositoryMetadata(
        url=repo_url,
        name=repo_name,
        total_files=len(files),
        languages_detected=sorted(list(languages)),
        files=files
    )
