from .models import Symbol
from .python_parser import parse_python_file
from .ts_parser import parse_ts_file
from pathlib import Path
from typing import List

def parse_file(file_path: Path, relative_path: str) -> List[Symbol]:
    ext = file_path.suffix.lower()
    if ext == ".py":
        return parse_python_file(file_path, relative_path)
    elif ext in (".js", ".jsx", ".ts", ".tsx"):
        return parse_ts_file(file_path, relative_path)
    return []

__all__ = ["Symbol", "parse_file", "parse_python_file", "parse_ts_file"]
