from pathlib import Path
from typing import List, Dict

from .models import Symbol
from .base import BaseParser
from .python_parser import PythonParser, parse_python_file
from .javascript_parser import JavaScriptParser, parse_js_file
from .typescript_parser import TypeScriptParser, parse_ts_file

PARSERS: Dict[str, BaseParser] = {
    ".py": PythonParser(),
    ".js": JavaScriptParser(),
    ".jsx": JavaScriptParser(),
    ".mjs": JavaScriptParser(),
    ".cjs": JavaScriptParser(),
    ".ts": TypeScriptParser(),
    ".tsx": TypeScriptParser(),
    ".mts": TypeScriptParser(),
    ".cts": TypeScriptParser(),
}

def parse_file(file_path: Path, relative_path: str) -> List[Symbol]:
    ext = file_path.suffix.lower()
    parser = PARSERS.get(ext)
    if parser:
        return parser.parse(file_path, relative_path)
    return []

__all__ = [
    "Symbol",
    "BaseParser",
    "PythonParser",
    "JavaScriptParser",
    "TypeScriptParser",
    "parse_file",
    "parse_python_file",
    "parse_js_file",
    "parse_ts_file",
    "PARSERS",
]
