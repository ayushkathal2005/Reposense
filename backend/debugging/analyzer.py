import json
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
import networkx as nx

from .models import (
    FailureLocation,
    DebugAnalysisResponse,
    DebugRequest
)
from .parser import ErrorTraceParser, ParsedError
from query.llm import LLMClient

class RepoDebugger:
    """Repository-Aware Debugging Intelligence Engine grounded in static knowledge graphs and source code."""

    def __init__(
        self,
        graph: nx.DiGraph,
        base_repo_path: Optional[Path] = None,
        llm: Optional[LLMClient] = None
    ):
        self.graph = graph if graph is not None else nx.DiGraph()
        self.base_repo_path = base_repo_path
        self.llm = llm

    def analyze(self, request: DebugRequest) -> DebugAnalysisResponse:
        parsed_err: ParsedError = ErrorTraceParser.parse(
            request.error_message,
            stack_trace=request.stack_trace
        )

        likely_locations: List[FailureLocation] = []
        facts: List[str] = []
        inferences: List[str] = []
        possible_causes: List[str] = []
        possible_fixes: List[str] = []
        related_callers: List[str] = []

        # 1. Resolve failure locations from parsed stack trace frames
        if parsed_err.frames:
            for frame in parsed_err.frames:
                norm_file = self._normalize_file_path(frame.file)
                snippet = self._read_source_snippet(norm_file, frame.line)
                likely_locations.append(
                    FailureLocation(
                        file=norm_file,
                        line=frame.line,
                        symbol=frame.symbol,
                        code_snippet=snippet,
                        relevance_score=1.0
                    )
                )
                loc_desc = f"`{norm_file}:{frame.line}`" if frame.line else f"`{norm_file}`"
                sym_desc = f" in symbol `{frame.symbol}`" if frame.symbol else ""
                facts.append(f"Traceback frame identifies failure location at {loc_desc}{sym_desc}.")

        # 2. If no stack trace frames, resolve using request hints and graph matching
        if not likely_locations:
            matched_syms = self._search_symbols(
                request.symbol,
                request.file_path,
                parsed_err.target_token
            )
            for sym_name, sym_attrs in matched_syms[:3]:
                sym_file = sym_attrs.get("file", "")
                sym_line = sym_attrs.get("start_line")
                snippet = self._read_source_snippet(sym_file, sym_line)
                likely_locations.append(
                    FailureLocation(
                        file=sym_file,
                        line=sym_line,
                        symbol=sym_name,
                        code_snippet=snippet,
                        relevance_score=0.85
                    )
                )
                facts.append(
                    f"Matched code symbol `{sym_name}` located in `{sym_file}` (lines {sym_attrs.get('start_line')}-{sym_attrs.get('end_line')})."
                )

        # 3. Discover Callers and Related Paths via Knowledge Graph
        for loc in likely_locations:
            if loc.symbol and loc.symbol in self.graph:
                incoming_callers = [
                    u for u, v, d in self.graph.in_edges(loc.symbol, data=True)
                    if d.get("relationship") in ("calls", "depends_on", "uses")
                ]
                for caller in incoming_callers:
                    caller_attrs = self.graph.nodes.get(caller, {})
                    c_file = caller_attrs.get("file", "")
                    c_line = caller_attrs.get("start_line", "")
                    ref_str = f"`{caller}`"
                    if c_file:
                        ref_str += f" ({c_file}:{c_line})"
                    if ref_str not in related_callers:
                        related_callers.append(ref_str)
                        facts.append(f"Caller `{caller}` invokes `{loc.symbol}`.")

        # 4. Search for relevant Schemas / Models if token exists
        token = parsed_err.target_token
        if token:
            facts.append(f"Target token extracted from error message: `{token}`.")
            schema_symbols = [
                n for n, d in self.graph.nodes(data=True)
                if d.get("type") in ("class", "model", "schema") and (
                    token.lower() in n.lower() or "user" in n.lower() or "order" in n.lower()
                )
            ]
            if schema_symbols:
                facts.append(f"Related domain schema/model defined in codebase: `{', '.join(schema_symbols[:2])}`.")

        # 5. Deterministic Cause, Inference, and Fix synthesis based on error type
        err_type = (parsed_err.error_type or "").lower()
        err_msg = parsed_err.error_message.lower()

        if "keyerror" in err_type or "keyerror" in err_msg:
            inferences.append(f"Dictionary or JSON payload accessed key `{token or 'specified key'}` without validating presence.")
            possible_causes.append(
                f"Missing key '{token or 'unknown'}' in dictionary payload; the caller did not supply this key or naming differs."
            )
            possible_fixes.append(
                f"Use `.get('{token or 'key'}', default)` or check key presence with `if '{token or 'key'}' in data:`."
            )
            possible_fixes.append(
                "Validate incoming request payload with a schema model (e.g. Pydantic) to ensure key presence at boundary."
            )
        elif "attributeerror" in err_type or "cannot read properties of undefined" in err_msg or "nullpointer" in err_type:
            inferences.append("Object reference is `None` or `undefined` when attribute/method was accessed.")
            possible_causes.append(
                "Upstream caller or repository lookup returned null/None, and no guard condition checked the result before dereferencing."
            )
            possible_fixes.append(
                "Add explicit null guard (`if obj is not None:` or optional chaining `obj?.prop`)."
            )
            possible_fixes.append(
                "Ensure upstream repository/service raises an explicit 404 or NotFoundException instead of propagating None."
            )
        elif "typeerror" in err_type:
            inferences.append("Argument count or type mismatch between caller invocation and function definition.")
            possible_causes.append(
                "Caller passed unexpected parameter types or insufficient arguments."
            )
            possible_fixes.append(
                "Verify signature compatibility and add type annotations or runtime assertions."
            )
        else:
            inferences.append(f"Runtime execution failure occurred during symbol execution for: {request.error_message}")
            possible_causes.append(
                f"Unchecked state or unexpected input data in {likely_locations[0].symbol if likely_locations else 'the target module'}."
            )
            possible_fixes.append(
                "Wrap invocation in a targeted try-except / try-catch block and log input parameters."
            )

        # 6. Confidence Assessment
        if parsed_err.frames and likely_locations:
            confidence = "High"
        elif likely_locations and related_callers:
            confidence = "Medium"
        else:
            confidence = "Low"
            if not facts:
                facts.append("No explicit traceback or symbol matches found in the knowledge graph.")

        # 7. Grounded Explanation
        explanation = self._build_explanation(
            request.error_message,
            likely_locations,
            facts,
            inferences,
            possible_causes,
            possible_fixes,
            related_callers,
            confidence
        )

        return DebugAnalysisResponse(
            error_summary=request.error_message,
            likely_locations=likely_locations,
            facts=facts,
            inferences=inferences,
            possible_causes=possible_causes,
            possible_fixes=possible_fixes,
            related_callers=related_callers,
            confidence=confidence,
            explanation=explanation,
            metadata={
                "error_type": parsed_err.error_type,
                "target_token": parsed_err.target_token,
                "parsed_frames_count": len(parsed_err.frames)
            }
        )

    def _normalize_file_path(self, raw_path: str) -> str:
        clean = raw_path.replace("\\", "/").strip()
        # Strip absolute prefix if matches base_repo_path
        if self.base_repo_path:
            base_str = str(self.base_repo_path).replace("\\", "/")
            if clean.startswith(base_str):
                clean = clean[len(base_str):].lstrip("/")
        return clean

    def _read_source_snippet(self, file_path: str, line: Optional[int], radius: int = 4) -> Optional[str]:
        if not file_path or not line or not self.base_repo_path:
            return None
        target_file = self.base_repo_path / file_path
        if not target_file.exists():
            return None
        try:
            lines = target_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            start = max(0, line - radius - 1)
            end = min(len(lines), line + radius)
            snippet_lines = []
            for i in range(start, end):
                prefix = ">> " if (i + 1) == line else "   "
                snippet_lines.append(f"{prefix}{i+1:4d} | {lines[i]}")
            return "\n".join(snippet_lines)
        except Exception:
            return None

    def _search_symbols(
        self,
        symbol_hint: Optional[str],
        file_hint: Optional[str],
        token: Optional[str]
    ) -> List[Tuple[str, Dict[str, Any]]]:
        candidates: List[Tuple[str, Dict[str, Any]]] = []

        for node, attrs in self.graph.nodes(data=True):
            if attrs.get("type") in ("file", "repository"):
                continue

            node_file = attrs.get("file", "")
            # Hint matching
            if symbol_hint and (node == symbol_hint or node.endswith(f".{symbol_hint}")):
                candidates.append((node, attrs))
                continue

            if file_hint and file_hint in node_file:
                if token and (token in node.lower() or token in str(attrs.get("docstring", "")).lower()):
                    candidates.append((node, attrs))
                    continue

            # Token matching
            if token and (token.lower() in node.lower()):
                candidates.append((node, attrs))

        return candidates

    def _build_explanation(
        self,
        error_msg: str,
        locations: List[FailureLocation],
        facts: List[str],
        inferences: List[str],
        causes: List[str],
        fixes: List[str],
        callers: List[str],
        confidence: str
    ) -> str:
        lines = [
            "### Debug Analysis",
            f"**Error:** `{error_msg}`",
            f"**Confidence:** `{confidence}`\n"
        ]

        if locations:
            lines.append("**Likely Failure Location(s):**")
            for loc in locations:
                line_str = f":{loc.line}" if loc.line else ""
                sym_str = f" in `{loc.symbol}`" if loc.symbol else ""
                lines.append(f"- `{loc.file}{line_str}`{sym_str}")
                if loc.code_snippet:
                    lines.append("```\n" + loc.code_snippet + "\n```")
            lines.append("")

        if facts:
            lines.append("**FACTS (Verified Code & Graph Evidence):**")
            for f in facts:
                lines.append(f"- {f}")
            lines.append("")

        if inferences:
            lines.append("**INFERENCES (Architectural Deductions):**")
            for inf in inferences:
                lines.append(f"- {inf}")
            lines.append("")

        if causes:
            lines.append("**POSSIBLE CAUSES:**")
            for c in causes:
                lines.append(f"- {c}")
            lines.append("")

        if callers:
            lines.append("**RELATED CALLERS:**")
            for clr in callers[:5]:
                lines.append(f"- {clr}")
            lines.append("")

        if fixes:
            lines.append("**RECOMMENDED FIXES:**")
            for fix in fixes:
                lines.append(f"- {fix}")

        summary = "\n".join(lines)

        # Grounded Gemini explanation if LLM client available
        if self.llm:
            prompt = (
                "SYSTEM INSTRUCTION: You are RepoSense's repository-aware debugging engine.\n"
                "Synthesize a crisp, highly actionable root-cause analysis based STRICTLY on the facts and code evidence below.\n"
                "Explicitly maintain the distinction between FACT, INFERENCE, and POSSIBLE CAUSE.\n"
                "Never invent files, libraries, or symbols not present in the evidence.\n\n"
                f"{summary}\n\n"
                "Provide a developer-ready diagnosis and recommended patch."
            )
            try:
                llm_response = self.llm.generate(prompt)
                if llm_response and not llm_response.startswith("Error:"):
                    return f"{summary}\n\n**Grounded Diagnostic Assessment:**\n{llm_response}"
            except Exception:
                pass

        return summary
