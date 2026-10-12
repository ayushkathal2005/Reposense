import networkx as nx
from typing import Dict, List, Set, Optional, Tuple, Any
from .models import DependentItem, ImpactAnalysisResponse
from query.llm import LLMClient

class ChangeImpactAnalyzer:
    def __init__(self, graph: nx.DiGraph, llm: Optional[LLMClient] = None):
        self.graph = graph if graph is not None else nx.DiGraph()
        self.llm = llm

    def resolve_symbol(self, query: str, file_path: Optional[str] = None) -> Optional[str]:
        """Resolves target symbol node in knowledge graph."""
        if not self.graph or not query:
            return None

        clean = query.strip()
        # 1. Exact node match
        if clean in self.graph:
            return clean

        # 2. Match with file_path hint
        if file_path:
            for node, attrs in self.graph.nodes(data=True):
                if attrs.get("file") == file_path and (node == clean or node.endswith(f".{clean}")):
                    return node

        # 3. Suffix match (e.g. "process_payment" -> "PaymentService.process_payment")
        suffix_matches = [
            node for node, attrs in self.graph.nodes(data=True)
            if attrs.get("type") not in ("file", "repository")
            and (node == clean or node.endswith(f".{clean}") or clean in node)
        ]
        if suffix_matches:
            # Sort by length similarity
            suffix_matches.sort(key=lambda s: len(s))
            return suffix_matches[0]

        return None

    def analyze(
        self,
        symbol_query: str,
        file_path: Optional[str] = None,
        max_depth: int = 6,
        explain: bool = True
    ) -> ImpactAnalysisResponse:
        """
        Computes the complete downstream blast radius of modifying a symbol
        using reverse graph traversal along calls, depends_on, and inherits edges.
        """
        target = self.resolve_symbol(symbol_query, file_path)
        if not target:
            return ImpactAnalysisResponse(
                target_symbol=symbol_query,
                risk_level="LOW",
                risk_score=0.0,
                risk_factors=["Symbol was not found in the repository knowledge graph."],
                blast_radius_count=0,
                explanation=f"Cannot establish change impact: '{symbol_query}' was not located in the indexed graph."
            )

        target_attrs = self.graph.nodes.get(target, {})
        target_file = target_attrs.get("file")

        # 1. Reverse graph traversal (BFS incoming edges)
        direct_dependents: List[DependentItem] = []
        indirect_dependents: List[DependentItem] = []
        visited: Set[str] = {target}
        queue: List[Tuple[str, int]] = [(target, 0)]

        affected_files: Set[str] = set()
        if target_file:
            affected_files.add(target_file)

        affected_apis: Set[str] = set()
        affected_tests: Set[str] = set()

        while queue:
            curr, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            # Incoming dependency edges: callers or dependents of curr
            incoming = [
                (u, d) for u, v, d in self.graph.in_edges(curr, data=True)
                if d.get("relationship") in ("calls", "depends_on", "inherits", "uses")
            ]

            for u, edge_data in incoming:
                u_attrs = self.graph.nodes.get(u, {})
                if u_attrs.get("type") in ("file", "repository"):
                    continue

                rel = edge_data.get("relationship", "calls")
                file_loc = u_attrs.get("file")
                ntype = u_attrs.get("type")

                # Check if API endpoint
                if ntype == "endpoint" or u_attrs.get("route_path") or (file_loc and "api/" in file_loc.lower()):
                    affected_apis.add(u)

                # Check if test file or function
                if (file_loc and ("test" in file_loc.lower() or "spec" in file_loc.lower())) or u.startswith("test_"):
                    affected_tests.add(u)

                if file_loc:
                    affected_files.add(file_loc)

                if u not in visited:
                    visited.add(u)
                    dep_item = DependentItem(
                        symbol=u,
                        type=ntype,
                        file=file_loc,
                        start_line=u_attrs.get("start_line"),
                        end_line=u_attrs.get("end_line"),
                        relationship=rel,
                        depth=depth + 1
                    )
                    if depth + 1 == 1:
                        direct_dependents.append(dep_item)
                    else:
                        indirect_dependents.append(dep_item)

                    queue.append((u, depth + 1))

        # 2. Deterministic Risk Assessment
        total_dependents = len(direct_dependents) + len(indirect_dependents)
        risk_factors: List[str] = []

        if affected_apis:
            risk_factors.append(f"Public API consumer(s) impacted: {', '.join(list(affected_apis)[:3])}")
        if any(d.type == "database_model" for d in direct_dependents + indirect_dependents):
            risk_factors.append("Downstream database-facing component or entity impacted")
        if len(affected_files) >= 3:
            risk_factors.append(f"Cross-module blast radius across {len(affected_files)} source files")
        if total_dependents >= 5:
            risk_factors.append(f"High fan-in: {total_dependents} downstream components rely on this symbol")
        if not affected_tests and total_dependents > 0:
            risk_factors.append("No automated test coverage detected in the downstream call hierarchy")

        # Determine level & score
        if total_dependents >= 8 or (affected_apis and len(affected_files) >= 3):
            risk_level = "CRITICAL"
            risk_score = 9.0
        elif total_dependents >= 4 or affected_apis:
            risk_level = "HIGH"
            risk_score = 7.5
        elif total_dependents >= 2 or len(affected_files) >= 2:
            risk_level = "MEDIUM"
            risk_score = 5.0
        else:
            risk_level = "LOW"
            risk_score = 2.0
            if not risk_factors:
                risk_factors.append("Isolated change: minimal or no downstream callers detected")

        # 3. Grounded Explanation
        explanation = None
        if explain:
            explanation = self._synthesize_explanation(
                target, target_file, risk_level, risk_factors,
                direct_dependents, indirect_dependents,
                list(affected_apis), list(affected_tests)
            )

        return ImpactAnalysisResponse(
            target_symbol=target,
            risk_level=risk_level,
            risk_score=risk_score,
            risk_factors=risk_factors,
            direct_dependents=direct_dependents,
            indirect_dependents=indirect_dependents,
            affected_files=sorted(list(affected_files)),
            affected_apis=sorted(list(affected_apis)),
            affected_tests=sorted(list(affected_tests)),
            blast_radius_count=total_dependents,
            explanation=explanation,
            metadata={
                "direct_count": len(direct_dependents),
                "indirect_count": len(indirect_dependents),
                "file_count": len(affected_files)
            }
        )

    def _synthesize_explanation(
        self,
        target: str,
        target_file: Optional[str],
        risk_level: str,
        risk_factors: List[str],
        direct: List[DependentItem],
        indirect: List[DependentItem],
        apis: List[str],
        tests: List[str]
    ) -> str:
        """Synthesizes an evidence-grounded summary of the change impact."""
        lines = [
            f"### Change Impact Analysis for `{target}`",
            f"**Assessed Risk Level:** `{risk_level}`\n",
            "**Key Risk Drivers:**"
        ]
        for f in risk_factors:
            lines.append(f"- {f}")

        if direct:
            lines.append(f"\n**Direct Callers ({len(direct)}):**")
            for d in direct[:5]:
                loc = f" (`{d.file}:{d.start_line}`)" if d.file and d.start_line else ""
                lines.append(f"- `{d.symbol}` [{d.relationship}]{loc}")

        if indirect:
            lines.append(f"\n**Indirect Dependent Components ({len(indirect)}):**")
            for d in indirect[:5]:
                lines.append(f"- `{d.symbol}` (depth {d.depth})")

        deterministic_summary = "\n".join(lines)

        # Grounded LLM narrative if client available
        if self.llm:
            prompt = (
                "SYSTEM INSTRUCTION: You are RepoSense's change impact analysis engine.\n"
                "Explain the potential impact of modifying the specified symbol based ONLY on the verified evidence below.\n"
                "Never invent dependencies or downstream effects not present in the evidence.\n\n"
                f"{deterministic_summary}\n\n"
                "Provide a concise, practical engineering assessment for the developer modifying this symbol."
            )
            try:
                narrative = self.llm.generate(prompt)
                if narrative and not narrative.startswith("Error:"):
                    return f"{deterministic_summary}\n\n**Impact Assessment:**\n{narrative}"
            except Exception:
                pass

        return deterministic_summary
