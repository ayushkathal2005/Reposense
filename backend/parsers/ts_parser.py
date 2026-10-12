# Re-export from typescript_parser for backwards compatibility
from .typescript_parser import parse_ts_file, TypeScriptParser, TS_LANGUAGE, TSX_LANGUAGE

__all__ = ["parse_ts_file", "TypeScriptParser", "TS_LANGUAGE", "TSX_LANGUAGE"]
