from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
import networkx as nx

from .models import SymbolDoc, DocumentationResponse, DocRequest
from query.llm import LLMClient

class RepoDocGenerator:
    """Generates evidence-backed API, function, module, and architecture documentation."""

    def __init__(
        self,
        graph: nx.DiGraph,
        base_repo_path: Optional[Path] = None,
        llm: Optional[LLMClient] = None
    ):
        self.graph = graph if graph is not None else nx.DiGraph()
        self.base_repo_path = base_repo_path
        self.llm = llm

    def generate(self, req: DocRequest) -> DocumentationResponse:
        doc_type = (req.doc_type or "api").lower()
        target = (req.target or "").strip()

        if doc_type == "api":
            return self._generate_api_doc(target)
        elif doc_type == "function":
            return self._generate_function_doc(target)
        elif doc_type == "module":
            return self._generate_module_doc(target)
        elif doc_type == "architecture":
            return self._generate_architecture_doc(target)
        else:
            return self._generate_api_doc(target)

    def _generate_api_doc(self, target: str) -> DocumentationResponse:
        # Find endpoint nodes
        endpoint_nodes = []
        for n, d in self.graph.nodes(data=True):
            if d.get("type") in ("route", "endpoint") or d.get("route_path"):
                endpoint_nodes.append((n, d))
            elif "api" in str(d.get("file", "")).lower() and d.get("type") in ("function", "method"):
                endpoint_nodes.append((n, d))

        if target:
            filtered = [
                (n, d) for n, d in endpoint_nodes
                if target in n or target in str(d.get("route_path", "")) or target in str(d.get("file", ""))
            ]
            if filtered:
                endpoint_nodes = filtered

        symbols_doc: List[SymbolDoc] = []
        lines: List[str] = [
            f"# API Documentation for Repository",
            f"**Indexed Endpoints:** {len(endpoint_nodes)}\n"
        ]

        mermaid_lines = ["flowchart TD"]

        for n, d in endpoint_nodes[:10]:
            r_path = d.get("route_path") or f"/{n}"
            r_method = d.get("route_method") or "ANY"
            f_path = d.get("file", "unknown")
            s_line = d.get("start_line")

            # Outgoing calls
            callees = [
                v for u, v, ed in self.graph.out_edges(n, data=True)
                if ed.get("relationship") in ("calls", "uses", "depends_on")
            ]
            # Incoming callers
            callers = [
                u for u, v, ed in self.graph.in_edges(n, data=True)
                if ed.get("relationship") in ("calls", "uses")
            ]

            sym_doc = SymbolDoc(
                name=n,
                type="endpoint",
                file=f_path,
                start_line=s_line,
                end_line=d.get("end_line"),
                docstring=d.get("docstring"),
                callees=callees,
                callers=callers,
                evidence_sources=[f"{f_path}:{s_line}" if s_line else f_path]
            )
            symbols_doc.append(sym_doc)

            lines.append(f"## `{r_method} {r_path}`")
            lines.append(f"- **Handler Symbol:** `{n}`")
            lines.append(f"- **File Location:** `{f_path}:{s_line or 1}`")
            if d.get("docstring"):
                lines.append(f"- **Description:** {d.get('docstring').strip()}")

            if callees:
                lines.append("- **Downstream Service / Controller Invocations:**")
                for callee in callees:
                    lines.append(f"  - `{callee}`")
                    clean_n = n.replace(".", "_").replace("/", "_")
                    clean_c = callee.replace(".", "_").replace("/", "_")
                    mermaid_lines.append(f'    {clean_n}["{r_method} {r_path}"] --> {clean_c}["{callee}"]')

            lines.append("")

        diagram = "\n".join(mermaid_lines) if len(mermaid_lines) > 1 else None
        md_text = "\n".join(lines)

        if self.llm:
            prompt = (
                "SYSTEM INSTRUCTION: You are RepoSense's documentation intelligence engine.\n"
                "Refine and enhance the following evidence-backed API documentation.\n"
                "Strictly preserve all verified routes, file paths, and downstream call references.\n"
                "Never invent external dependencies, headers, or query parameters not evidenced.\n\n"
                f"{md_text}"
            )
            try:
                enhanced = self.llm.generate(prompt)
                if enhanced and not enhanced.startswith("Error:"):
                    md_text = enhanced
            except Exception:
                pass

        return DocumentationResponse(
            title="Repository API Documentation",
            doc_type="api",
            target=target or "all_endpoints",
            markdown_content=md_text,
            symbols=symbols_doc,
            diagram_mermaid=diagram,
            metadata={"endpoint_count": len(endpoint_nodes)}
        )

    def _generate_function_doc(self, target: str) -> DocumentationResponse:
        matched_node = None
        for n in self.graph.nodes:
            if n == target or n.endswith(f".{target}") or target in n:
                matched_node = n
                break

        if not matched_node:
            # Fallback to first non-file node
            for n, d in self.graph.nodes(data=True):
                if d.get("type") not in ("file", "repository"):
                    matched_node = n
                    break

        if not matched_node:
            return DocumentationResponse(
                title=f"Documentation for '{target}'",
                doc_type="function",
                target=target,
                markdown_content=f"No symbols found matching '{target}'.",
                symbols=[]
            )

        d = self.graph.nodes.get(matched_node, {})
        callees = [v for u, v in self.graph.out_edges(matched_node)]
        callers = [u for u, v in self.graph.in_edges(matched_node)]

        sym_doc = SymbolDoc(
            name=matched_node,
            type=d.get("type", "function"),
            file=d.get("file"),
            start_line=d.get("start_line"),
            end_line=d.get("end_line"),
            docstring=d.get("docstring"),
            callees=callees,
            callers=callers,
            evidence_sources=[f"{d.get('file')}:{d.get('start_line')}"]
        )

        lines = [
            f"# Function / Symbol Documentation: `{matched_node}`\n",
            f"- **Type:** `{d.get('type', 'function')}`",
            f"- **File:** `{d.get('file')}`",
            f"- **Line Range:** {d.get('start_line')} - {d.get('end_line')}",
        ]
        if d.get("docstring"):
            lines.append(f"\n### Description\n{d.get('docstring').strip()}\n")

        if callers:
            lines.append("### Inward Callers (Incoming References)")
            for c in callers:
                lines.append(f"- `{c}`")
            lines.append("")

        if callees:
            lines.append("### Outward Invocations (Downstream Calls)")
            for c in callees:
                lines.append(f"- `{c}`")
            lines.append("")

        md_text = "\n".join(lines)
        return DocumentationResponse(
            title=f"Documentation: {matched_node}",
            doc_type="function",
            target=matched_node,
            markdown_content=md_text,
            symbols=[sym_doc]
        )

    def _generate_module_doc(self, target: str) -> DocumentationResponse:
        # Find all symbols in the target module / file
        symbols_in_module = []
        for n, d in self.graph.nodes(data=True):
            f = str(d.get("file", ""))
            if target and (target in f or target == f):
                symbols_in_module.append((n, d))
            elif not target and d.get("type") not in ("file", "repository"):
                symbols_in_module.append((n, d))

        lines = [
            f"# Module Documentation: `{target or 'Repository Root'}`\n",
            f"**Indexed Symbols in Scope:** {len(symbols_in_module)}\n"
        ]

        symbols_doc: List[SymbolDoc] = []
        for n, d in symbols_in_module[:20]:
            callees = [v for u, v in self.graph.out_edges(n)]
            sym_doc = SymbolDoc(
                name=n,
                type=d.get("type"),
                file=d.get("file"),
                start_line=d.get("start_line"),
                end_line=d.get("end_line"),
                docstring=d.get("docstring"),
                callees=callees
            )
            symbols_doc.append(sym_doc)
            lines.append(f"### `{n}` ({d.get('type')})")
            lines.append(f"- **Defined at:** `{d.get('file')}:{d.get('start_line')}`")
            if d.get("docstring"):
                lines.append(f"- **Summary:** {d.get('docstring').strip()}")
            if callees:
                lines.append(f"- **Calls:** {', '.join(f'`{c}`' for c in callees[:4])}")
            lines.append("")

        return DocumentationResponse(
            title=f"Module Documentation: {target}",
            doc_type="module",
            target=target,
            markdown_content="\n".join(lines),
            symbols=symbols_doc,
            metadata={"symbols_count": len(symbols_in_module)}
        )

    def _generate_architecture_doc(self, target: str) -> DocumentationResponse:
        # Categorize by layers
        layers: Dict[str, List[str]] = {
            "API / Routes": [],
            "Controllers": [],
            "Services / Business Logic": [],
            "Repositories / Data Access": [],
            "Entities / Models": [],
            "External Gateways / Clients": []
        }

        for n, d in self.graph.nodes(data=True):
            ntype = d.get("type", "")
            nfile = str(d.get("file", "")).lower()
            name_lower = n.lower()

            if ntype in ("route", "endpoint") or "api/" in nfile:
                layers["API / Routes"].append(n)
            elif "controller" in nfile or "controller" in name_lower:
                layers["Controllers"].append(n)
            elif "service" in nfile or "service" in name_lower:
                layers["Services / Business Logic"].append(n)
            elif "repo" in nfile or "repo" in name_lower:
                layers["Repositories / Data Access"].append(n)
            elif "model" in nfile or "schema" in nfile or ntype in ("class", "model"):
                layers["Entities / Models"].append(n)
            elif "client" in nfile or "gateway" in nfile or "stripe" in name_lower:
                layers["External Gateways / Clients"].append(n)

        lines = [
            "# Architecture Overview & Layer Documentation\n",
            "This architectural document is generated directly from the repository's static knowledge graph.\n"
        ]

        mermaid = [
            "flowchart TD",
            "    API[API Layer] --> Controllers[Controllers Layer]",
            "    Controllers --> Services[Services Layer]",
            "    Services --> Repos[Repositories Layer]",
            "    Repos --> DB[(Database / Persistence)]",
            "    Services --> External[External Gateways / APIs]"
        ]

        for layer_name, comps in layers.items():
            if comps:
                lines.append(f"## {layer_name} ({len(comps)} components)")
                for comp in comps[:5]:
                    lines.append(f"- `{comp}`")
                lines.append("")

        return DocumentationResponse(
            title="System Architecture Documentation",
            doc_type="architecture",
            target=target or "full_system",
            markdown_content="\n".join(lines),
            diagram_mermaid="\n".join(mermaid),
            metadata={"active_layers": [k for k, v in layers.items() if v]}
        )
