import networkx as nx
from typing import List, Optional, Set, Dict, Any, Tuple
from .models import TraceStep, ExecutionTrace
from query.llm import LLMClient

class ExecutionTracer:
    def __init__(self, graph: nx.DiGraph, llm: Optional[LLMClient] = None):
        self.graph = graph if graph is not None else nx.DiGraph()
        self.llm = llm

    def find_entrypoint(self, query_or_symbol: str) -> Optional[str]:
        """
        Locates the best candidate entrypoint node in the knowledge graph.
        Matches exact symbol name, route paths, methods, or candidate tokens.
        """
        if not self.graph or not query_or_symbol:
            return None

        clean_query = query_or_symbol.strip()

        # 1. Exact node match
        if clean_query in self.graph:
            return clean_query

        # 2. Match route path (e.g., "POST /api/orders" or "/api/orders")
        route_tokens = clean_query.split()
        target_path = route_tokens[-1] if route_tokens else clean_query
        for node, attrs in self.graph.nodes(data=True):
            if attrs.get("route_path") and attrs.get("route_path") == target_path:
                return node

        # 3. Match symbol name suffix (e.g. "create" -> "OrderController.create")
        suffix_matches = [
            node for node in self.graph.nodes
            if node.endswith(f".{clean_query}") or clean_query in node
        ]
        if suffix_matches:
            # Prefer functions/methods/endpoints
            for match in suffix_matches:
                ntype = self.graph.nodes[match].get("type")
                if ntype in ("endpoint", "function", "method"):
                    return match
            return suffix_matches[0]

        # 4. Token-based matching on endpoint/function nodes
        tokens = [t.lower() for t in clean_query.replace("/", " ").replace("_", " ").split() if len(t) > 2]
        best_node = None
        best_score = 0

        for node, attrs in self.graph.nodes(data=True):
            ntype = attrs.get("type", "")
            if ntype in ("endpoint", "function", "method", "class"):
                node_lower = node.lower()
                matched = sum(1 for t in tokens if t in node_lower)
                if matched > best_score:
                    best_score = matched
                    best_node = node

        return best_node if best_score > 0 else None

    def trace(
        self,
        entrypoint_query: str,
        target_symbol: Optional[str] = None,
        max_depth: int = 8,
        explain: bool = True
    ) -> ExecutionTrace:
        """
        Statically traces execution paths through the repository knowledge graph
        along 'calls' and 'exposes' edges.
        """
        entrypoint = self.find_entrypoint(entrypoint_query)
        if not entrypoint:
            return ExecutionTrace(
                entrypoint=entrypoint_query,
                steps=[],
                confidence="unresolved",
                unresolved_steps=[f"Could not establish entrypoint matching '{entrypoint_query}' in repository graph."],
                explanation="The repository knowledge graph does not contain a verified entrypoint matching the query."
            )

        # 1. Target-directed trace
        target_node = self.find_entrypoint(target_symbol) if target_symbol else None
        if target_node and entrypoint != target_node:
            try:
                # Find calls-only subgraph or general path
                calls_subgraph = nx.DiGraph([
                    (u, v, d) for u, v, d in self.graph.edges(data=True)
                    if d.get("relationship") in ("calls", "exposes", "defines")
                ])
                if nx.has_path(calls_subgraph, entrypoint, target_node):
                    path = nx.shortest_path(calls_subgraph, source=entrypoint, target=target_node)
                    return self._build_trace_from_path(entrypoint, path, explain=explain)
            except Exception:
                pass

        # 2. Forward execution flow exploration (DFS along calls edges)
        primary_path: List[str] = [entrypoint]
        alternative_paths_nodes: List[List[str]] = []
        unresolved_calls: List[str] = []
        visited: Set[str] = {entrypoint}

        def explore(current: str, depth: int, current_path: List[str]):
            if depth >= max_depth:
                return

            # Outgoing calls
            calls_edges = [
                (v, d) for u, v, d in self.graph.out_edges(current, data=True)
                if d.get("relationship") in ("calls", "exposes")
            ]

            valid_calls = [v for v, d in calls_edges if v not in visited and self.graph.nodes[v].get("type") != "file"]

            if not valid_calls:
                return

            # Follow primary branch
            next_node = valid_calls[0]
            visited.add(next_node)
            current_path.append(next_node)
            explore(next_node, depth + 1, current_path)

            # Record alternatives if multiple calls exist at this step
            if len(valid_calls) > 1:
                for alt_node in valid_calls[1:]:
                    if alt_node not in visited:
                        alt_branch = list(current_path[:-1]) + [alt_node]
                        alternative_paths_nodes.append(alt_branch)

        explore(entrypoint, 1, primary_path)

        # Build TraceStep items for primary path
        steps: List[TraceStep] = []
        for idx, node in enumerate(primary_path):
            attrs = self.graph.nodes[node]
            rel = "entrypoint" if idx == 0 else "calls"
            if idx > 0:
                edge_data = self.graph.get_edge_data(primary_path[idx - 1], node)
                if edge_data:
                    rel = edge_data.get("relationship", "calls")

            steps.append(TraceStep(
                step_number=idx + 1,
                symbol=node,
                type=attrs.get("type"),
                file=attrs.get("file"),
                start_line=attrs.get("start_line"),
                end_line=attrs.get("end_line"),
                relationship=rel,
                evidence=attrs.get("docstring")
            ))

        # Build alternative paths
        alt_traces: List[List[TraceStep]] = []
        for alt_path in alternative_paths_nodes[:3]:
            alt_steps = []
            for idx, node in enumerate(alt_path):
                attrs = self.graph.nodes[node]
                rel = "entrypoint" if idx == 0 else "calls"
                alt_steps.append(TraceStep(
                    step_number=idx + 1,
                    symbol=node,
                    type=attrs.get("type"),
                    file=attrs.get("file"),
                    start_line=attrs.get("start_line"),
                    end_line=attrs.get("end_line"),
                    relationship=rel,
                    evidence=attrs.get("docstring")
                ))
            alt_traces.append(alt_steps)

        # Confidence rating
        if len(steps) >= 3 and not unresolved_calls:
            confidence = "high"
        elif len(steps) >= 2:
            confidence = "medium"
        elif len(steps) == 1:
            confidence = "low"
        else:
            confidence = "unresolved"

        explanation = None
        if explain:
            explanation = self._generate_explanation(entrypoint, steps, alt_traces)

        return ExecutionTrace(
            entrypoint=entrypoint,
            steps=steps,
            confidence=confidence,
            unresolved_steps=unresolved_calls,
            alternative_paths=alt_traces,
            explanation=explanation,
            metadata={
                "total_steps": len(steps),
                "has_alternatives": len(alt_traces) > 0
            }
        )

    def _build_trace_from_path(self, entrypoint: str, path: List[str], explain: bool = True) -> ExecutionTrace:
        steps: List[TraceStep] = []
        for idx, node in enumerate(path):
            attrs = self.graph.nodes[node]
            rel = "entrypoint" if idx == 0 else "calls"
            if idx > 0:
                edge_data = self.graph.get_edge_data(path[idx - 1], node)
                if edge_data:
                    rel = edge_data.get("relationship", "calls")

            steps.append(TraceStep(
                step_number=idx + 1,
                symbol=node,
                type=attrs.get("type"),
                file=attrs.get("file"),
                start_line=attrs.get("start_line"),
                end_line=attrs.get("end_line"),
                relationship=rel,
                evidence=attrs.get("docstring")
            ))

        explanation = self._generate_explanation(entrypoint, steps, []) if explain else None

        return ExecutionTrace(
            entrypoint=entrypoint,
            steps=steps,
            confidence="high" if len(steps) >= 2 else "medium",
            unresolved_steps=[],
            alternative_paths=[],
            explanation=explanation,
            metadata={"total_steps": len(steps)}
        )

    def _generate_explanation(
        self,
        entrypoint: str,
        steps: List[TraceStep],
        alternatives: List[List[TraceStep]]
    ) -> str:
        """
        Synthesizes a grounded explanation of the statically verified execution path.
        Uses LLM if available; falls back to structured markdown description.
        """
        if not steps:
            return "No execution path established."

        # Deterministic structured summary
        summary_lines = [
            f"Execution flow initiates at entrypoint `{entrypoint}` and traverses {len(steps)} verified steps:"
        ]
        for step in steps:
            loc = f" (`{step.file}:{step.start_line}`)" if step.file and step.start_line else ""
            summary_lines.append(f"{step.step_number}. **{step.symbol}** [{step.relationship}]{loc}")
            if step.evidence:
                summary_lines.append(f"   - *Note:* {step.evidence}")

        if alternatives:
            summary_lines.append(f"\n*{len(alternatives)} alternative execution branch(es) detected in the code graph.*")

        deterministic_summary = "\n".join(summary_lines)

        # If LLM client is available, synthesize grounded narrative
        if self.llm:
            prompt = (
                "SYSTEM INSTRUCTION: You are RepoSense's execution flow explanation engine.\n"
                "Explain the following verified codebase execution path step-by-step.\n"
                "The path was statically verified from the repository code graph.\n"
                "DO NOT invent any steps, functions, files, or execution hops that are not in the trace below.\n"
                "Explain how the components interact based strictly on the sequence provided.\n\n"
                f"Entrypoint: {entrypoint}\n\n"
                f"Statically Verified Steps:\n{deterministic_summary}\n\n"
                "Provide a clear, grounded explanation of this workflow."
            )
            try:
                llm_response = self.llm.generate(prompt)
                if llm_response and not llm_response.startswith("Error:"):
                    return f"{deterministic_summary}\n\n### Flow Explanation\n{llm_response}"
            except Exception:
                pass

        return deterministic_summary
