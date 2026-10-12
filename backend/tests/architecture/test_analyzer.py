import pytest
import networkx as nx
from architecture.analyzer import ArchitectureAnalyzer
from parsers.models import Symbol
from graph.builder import build_knowledge_graph

@pytest.fixture
def multi_tier_app_graph():
    symbols = [
        Symbol(
            type="route",
            name="order_endpoint",
            file="api/order_routes.py",
            start_line=1,
            end_line=20,
            route_path="/api/orders",
            route_method="POST",
            calls=["OrderController"]
        ),
        Symbol(
            type="class",
            name="OrderController",
            file="controllers/order_controller.py",
            start_line=1,
            end_line=50,
            calls=["OrderService"]
        ),
        Symbol(
            type="class",
            name="OrderService",
            file="services/order_service.py",
            start_line=1,
            end_line=60,
            calls=["OrderRepository", "StripeClient"]
        ),
        Symbol(
            type="class",
            name="OrderRepository",
            file="repositories/order_repository.py",
            start_line=1,
            end_line=40,
            calls=["OrderModel"]
        ),
        Symbol(
            type="class",
            name="OrderModel",
            file="models/order.py",
            start_line=1,
            end_line=30,
            dependencies=["BaseModel"]
        ),
        Symbol(
            type="class",
            name="StripeClient",
            file="gateways/stripe_client.py",
            start_line=1,
            end_line=35
        ),
    ]
    return build_knowledge_graph(symbols, repo_id="ecommerce_app")

def test_architecture_layer_classification(multi_tier_app_graph):
    analyzer = ArchitectureAnalyzer(multi_tier_app_graph)
    report = analyzer.analyze()

    assert "api" in report.layers
    assert "order_endpoint" in report.layers["api"]

    assert "controller" in report.layers
    assert "OrderController" in report.layers["controller"]

    assert "service" in report.layers
    assert "OrderService" in report.layers["service"]

    assert "repository" in report.layers
    assert "OrderRepository" in report.layers["repository"]

    assert "database" in report.layers
    assert "OrderModel" in report.layers["database"]

    assert "external_service" in report.layers
    assert "StripeClient" in report.layers["external_service"]

def test_mermaid_generation(multi_tier_app_graph):
    analyzer = ArchitectureAnalyzer(multi_tier_app_graph)
    report = analyzer.analyze()

    mermaid = report.mermaid_diagram
    assert "flowchart TD" in mermaid
    assert "subgraph" in mermaid
    assert "OrderController" in mermaid
    assert "OrderService" in mermaid
    assert "-->" in mermaid

    layer_mermaid = report.layer_diagram
    assert "flowchart LR" in layer_mermaid
    assert "API Endpoints" in layer_mermaid

def test_relationships_count(multi_tier_app_graph):
    analyzer = ArchitectureAnalyzer(multi_tier_app_graph)
    report = analyzer.analyze()

    rels = report.relationships
    assert len(rels) > 0

    # Verify calls link from Controller to Service
    controller_calls = [r for r in rels if r.source == "OrderController" and r.target == "OrderService"]
    assert len(controller_calls) > 0
    assert controller_calls[0].source_role == "controller"
    assert controller_calls[0].target_role == "service"

def test_empty_graph():
    G = nx.DiGraph()
    analyzer = ArchitectureAnalyzer(G)
    report = analyzer.analyze()

    assert len(report.components) == 0
    assert len(report.relationships) == 0
    assert "flowchart TD" in report.mermaid_diagram
    assert report.summary["total_components"] == 0
