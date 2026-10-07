import pytest
from pathlib import Path
from ingestion.detector import ingest_directory, detect_language

def test_detect_language():
    assert detect_language(Path("test.py")) == "Python"
    assert detect_language(Path("app.js")) == "JavaScript"
    assert detect_language(Path("main.ts")) == "TypeScript"
    assert detect_language(Path("component.tsx")) == "TypeScript"
    assert detect_language(Path("unknown.xyz")) is None

def test_ingest_directory(tmp_path):
    # Setup mock repository
    (tmp_path / "src").mkdir()
    (tmp_path / "node_modules").mkdir()
    
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "src" / "index.js").write_text("console.log('hello')")
    (tmp_path / ".env").write_text("SECRET=123")
    (tmp_path / "node_modules" / "test.js").write_text("ignore me")
    
    metadata = ingest_directory("https://github.com/test/repo", "repo", tmp_path)
    
    assert metadata.name == "repo"
    assert metadata.total_files == 2  # main.py and src/index.js
    assert set(metadata.languages_detected) == {"Python", "JavaScript"}
    
    paths = {f.path for f in metadata.files}
    assert "main.py" in paths
    assert "src/index.js" in paths
    assert ".env" not in paths
    assert "node_modules/test.js" not in paths
