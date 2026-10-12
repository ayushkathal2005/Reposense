import re
import networkx as nx
from typing import Dict, List, Set, Any, Optional, Tuple
from .models import ArchitectureComponent, ArchitectureRelationship, ArchitectureReport

ROLE_LABELS = {
    "api": "API Endpoints",
    "controller": "Controllers",
    "service": "Business Services",
    "repository": "Repositories & Data Access",
    "database": "Database Models",
    "external_service": "External Clients & Gateways",
    "frontend": "Frontend Components",
    "utility": "Utilities & Modules"
}

def sanitize_id(name: str) -> str:
    """Creates a valid Mermaid node identifier."""
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    if sanitized and sanitized[0].isdigit():
        sanitized = "n_" + sanitized
    return sanitized or "node"

class ArchitectureAnalyzer:
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph if graph is not None else nx.DiGraph()

    def classify_node(self, node_name: str, attrs: Dict[str, Any]) -> str:
        """
        Classifies a node into an architectural layer based strictly on static evidence
        such as node type, decorators, route paths, file path, and naming patterns.
        """
        file_path = (attrs.get("file") or "").lower()
        node_lower = node_name.lower()
        ntype = attrs.get("type", "")

        # 1. API / Routes
        if ntype == "endpoint" or attrs.get("route_path") or "api/" in file_path or "routes/" in file_path:
            return "api"

        # 2. Controllers
        if node_name.endswith("Controller") or "controllers/" in file_path or "controller" in node_lower:
            return "controller"

        # 3. Services
        if any(node_name.endswith(s) for s in ("Service", "Manager", "Processor", "Handler")) or "services/" in file_path:
            return "service"

        # 4. Repositories
        if any(node_name.endswith(r) for r in ("Repository", "Store", "Dao")) or "repositories/" in file_path:
            return "repository"

        # 5. Database Models
        if ntype == "database_model" or node_name.endswith("Model") or "models/" in file_path or "db/" in file_path:
            return "database"

        # 6. External Services / Gateways / Clients
        if any(node_name.endswith(e) for e in ("Client", "Gateway", "Provider", "Adapter")) or any(p in file_path for p in ("gateways/", "clients/", "external/")):
            return "external_service"

        # 7. Frontend
        if file_path.endswith((".tsx", ".jsx", ".vue", ".svelte")) or any(f in file_path for f in ("frontend/", "components/", "pages/", "views/")):
            return "frontend"

        return "utility"

    def analyze(self) -> ArchitectureReport:
        """
        Extracts components, roles, and inter-component interactions from the graph,
        and generates evidence-backed Mermaid diagrams.
        """
        components: List[ArchitectureComponent] = []
        layers: Dict[str, List[str]] = {role: [] for role in ROLE_LABELS}
        role_map: Dict[str, str] = {}

        # 1. Classify all non-file symbol nodes
        for node_name, attrs in self.graph.nodes(data=True):
            if attrs.get("type") == "file" or attrs.get("type") == "repository":
                continue

            role = self.classify_node(node_name, attrs)
            role_map[node_name] = role
            layers[role].append(node_name)

            # Discover outgoing calls
            outgoing = [
                v for u, v, d in self.graph.out_edges(node_name, data=True)
                if d.get("relationship") in ("calls", "depends_on", "inherits", "exposes")
                and self.graph.nodes[v].get("type") not in ("file", "repository")
            ]

            components.append(ArchitectureComponent(
                id=sanitize_id(node_name),
                name=node_name,
                role=role,
                file=attrs.get("file"),
                start_line=attrs.get("start_line"),
                end_line=attrs.get("end_line"),
                docstring=attrs.get("docstring"),
                outgoing_calls=outgoing
            ))

        # 2. Extract Relationships
        rel_map: Dict[Tuple[str, str], int] = {}
        layer_interactions: Set[Tuple[str, str]] = set()

        for u, v, data in self.graph.edges(data=True):
            rel = data.get("relationship", "calls")
            if rel in ("calls", "depends_on", "inherits", "exposes"):
                u_type = self.graph.nodes[u].get("type") if u in self.graph else ""
                v_type = self.graph.nodes[v].get("type") if v in self.graph else ""
                if u_type not in ("file", "repository") and v_type not in ("file", "repository"):
                    rel_map[(u, v)] = rel_map.get((u, v), 0) + 1
                    u_role = role_map.get(u, "utility")
                    v_role = role_map.get(v, "utility")
                    if u_role != v_role:
                        layer_interactions.add((u_role, v_role))

        relationships: List[ArchitectureRelationship] = []
        for (u, v), count in rel_map.items():
            relationships.append(ArchitectureRelationship(
                source=u,
                target=v,
                source_role=role_map.get(u, "utility"),
                target_role=role_map.get(v, "utility"),
                relationship="calls",
                call_count=count
            ))

        # 3. Generate Mermaid Diagrams
        mermaid_diagram = self._generate_component_mermaid(layers, rel_map)
        layer_diagram = self._generate_layer_mermaid(layer_interactions, layers)

        # 4. Summary metrics
        active_layers = {r: len(nodes) for r, nodes in layers.items() if len(nodes) > 0}
        summary = {
            "total_components": len(components),
            "total_relationships": len(relationships),
            "active_layer_count": len(active_layers),
            "layer_distribution": active_layers
        }

        return ArchitectureReport(
            components=components,
            relationships=relationships,
            layers=layers,
            mermaid_diagram=mermaid_diagram,
            layer_diagram=layer_diagram,
            summary=summary
        )

    def _generate_component_mermaid(
        self,
        layers: Dict[str, List[str]],
        rel_map: Dict[Tuple[str, str], int]
    ) -> str:
        """Generates evidence-backed component-level Mermaid diagram."""
        lines = ["flowchart TD"]

        # Subgraphs per active layer
        for role, nodes in layers.items():
            if not nodes:
                continue
            subgraph_id = sanitize_id(role)
            label = ROLE_LABELS.get(role, role.capitalize())
            lines.append(f'    subgraph {subgraph_id} ["{label}"]')
            for node in nodes[:15]:  # Bounded to avoid diagram clutter
                nid = sanitize_id(node)
                safe_name = node.replace('"', '\\"')
                lines.append(f'        {nid}["{safe_name}"]')
            lines.append("    end")

        # Edges between components
        for (u, v), count in list(rel_map.items())[:30]:
            uid = sanitize_id(u)
            vid = sanitize_id(v)
            lines.append(f"    {uid} --> {vid}")

        return "\n".join(lines)

    def _generate_layer_mermaid(
        self,
        interactions: Set[Tuple[str, str]],
        layers: Dict[str, List[str]]
    ) -> str:
        """Generates high-level layer-to-layer architectural diagram."""
        lines = ["flowchart LR"]

        active_roles = [r for r, nodes in layers.items() if len(nodes) > 0]
        for role in active_roles:
            rid = sanitize_id(role)
            label = ROLE_LABELS.get(role, role.capitalize())
            lines.append(f'    {rid}["{label}"]')

        for u_role, v_role in interactions:
            uid = sanitize_id(u_role)
            vid = sanitize_id(v_role)
            lines.append(f"    {uid} --> {vid}")

        return "\n".join(lines)
