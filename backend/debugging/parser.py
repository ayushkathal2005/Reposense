import re
from typing import List, Dict, Optional, Any
from pydantic import BaseModel

class ParsedFrame(BaseModel):
    file: str
    line: Optional[int] = None
    symbol: Optional[str] = None
    code_snippet: Optional[str] = None

class ParsedError(BaseModel):
    error_type: Optional[str] = None
    error_message: str
    target_token: Optional[str] = None
    frames: List[ParsedFrame] = []

class ErrorTraceParser:
    """Parses stack traces and runtime error messages across Python, JS, and TS."""

    PYTHON_FRAME_REGEX = re.compile(
        r'File\s+["\'](?P<file>[^"\']+)["\'],\s+line\s+(?P<line>\d+)(?:,\s+in\s+(?P<symbol>[^\n\r]+))?'
    )
    JS_FRAME_REGEX = re.compile(
        r'at\s+(?:(?P<symbol>[^\s(]+)\s+\()?(?P<file>[^:\s()]+):(?P<line>\d+)(?::\d+)?\)?'
    )
    ERROR_TYPE_REGEX = re.compile(
        r'^(?P<type>[A-Za-z_][A-Za-z0-9_]*(?:Error|Exception|Fault)?):\s*(?P<msg>.*)$',
        re.MULTILINE
    )

    @classmethod
    def parse(cls, error_text: str, stack_trace: Optional[str] = None) -> ParsedError:
        combined = f"{error_text}\n{stack_trace or ''}".strip()
        frames: List[ParsedFrame] = []

        # 1. Extract Python frames
        for match in cls.PYTHON_FRAME_REGEX.finditer(combined):
            file_path = match.group("file").replace("\\", "/")
            line_num = int(match.group("line")) if match.group("line") else None
            sym = match.group("symbol").strip() if match.group("symbol") else None
            frames.append(ParsedFrame(file=file_path, line=line_num, symbol=sym))

        # 2. Extract JS/TS frames
        for match in cls.JS_FRAME_REGEX.finditer(combined):
            file_path = match.group("file").replace("\\", "/")
            line_num = int(match.group("line")) if match.group("line") else None
            sym = match.group("symbol").strip() if match.group("symbol") else None
            frames.append(ParsedFrame(file=file_path, line=line_num, symbol=sym))

        # 3. Extract Error Type and Message
        err_type = None
        err_msg = error_text.strip()
        type_match = cls.ERROR_TYPE_REGEX.search(error_text)
        if type_match:
            err_type = type_match.group("type")
            err_msg = type_match.group("msg").strip()
        elif ":" in error_text:
            parts = error_text.split(":", 1)
            candidate = parts[0].strip()
            if " " not in candidate and len(candidate) > 2:
                err_type = candidate
                err_msg = parts[1].strip()

        # 4. Extract token of interest (e.g. 'user_id' in KeyError: 'user_id')
        token = None
        token_match = re.search(r"['\"](?P<token>[A-Za-z0-9_\-\.]+)['\"]", err_msg)
        if token_match:
            token = token_match.group("token")
        else:
            # Check for words like user_id in KeyError: user_id
            words = err_msg.split()
            if len(words) == 1 and re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', words[0]):
                token = words[0]

        return ParsedError(
            error_type=err_type,
            error_message=err_msg or error_text,
            target_token=token,
            frames=frames
        )
