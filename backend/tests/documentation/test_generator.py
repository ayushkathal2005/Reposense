import pytest
import networkx as nx
from documentation.generator import RepoDocGenerator
from documentation.models import DocRequest, DocumentationResponse
from parsers.models import Symbol
from graph.builder import build_knowledge_graph

@pytest.fixture
def orders_service_graph():
    symbols = [
        Symbol(
            type="route",
            name="create_order_endpoint",
            file="src/api/orders.py",
            start_line=10,
            end_line=25,
            route_path="/api/orders",
            route_method="POST",
            docstring="Creates a new customer order.",
            calls=["OrderController.create"]
        ),
        Symbol(
            type="method",
            name="OrderController.create",
            file="src/controllers/order_controller.py",
            start_line=15,
            end_line=45,
            calls=["OrderService.create_order"]
        ),
        Symbol(
            type="method",
            name="OrderService.create_order",
            file="src/services/order_service.py",
            start_line=20,
            end_line=75,
            docstring="Processes cart validation and initiates payment.",
            calls=["PaymentService.charge", "OrderRepository.save"]
        ),
        Symbol(
            type="method",
            name="PaymentService.charge",
            file="src/services/payment_service.py",
            start_line=10,
            end_line=30
        ),
        Symbol(
            type="method",
            name="OrderRepository.save",
            file="src/repositories/order_repo.py",
            start_line=5,
            end_line=25
        ),
    ]
    return build_knowledge_graph(symbols, repo_id="orders_app")


def test_generate_api_documentation(orders_service_graph):
    generator = RepoDocGenerator(orders_service_graph)
    req = DocRequest(repo_id="orders_app", doc_type="api")
    res = generator.generate(req)

    assert isinstance(res, DocumentationResponse)
    assert res.doc_type == "api"
    assert "POST /api/orders" in res.markdown_content
    assert "create_order_endpoint" in res.markdown_content
    assert "OrderController.create" in res.markdown_content
    assert res.diagram_mermaid is not None
    assert "flowchart TD" in res.diagram_mermaid
    assert len(res.symbols) >= 1


def test_generate_function_documentation(orders_service_graph):
    generator = RepoDocGenerator(orders_service_graph)
    req = DocRequest(
        repo_id="orders_app",
        target="OrderService.create_order",
        doc_type="function"
    )
    res = generator.generate(req)

    assert res.doc_type == "function"
    assert "OrderService.create_order" in res.markdown_content
    assert "Inward Callers" in res.markdown_content
    assert "OrderController.create" in res.markdown_content
    assert "PaymentService.charge" in res.markdown_content
    assert "OrderRepository.save" in res.markdown_content
    assert len(res.symbols) == 1
    assert res.symbols[0].file == "src/services/order_service.py"


def test_generate_module_documentation(orders_service_graph):
    generator = RepoDocGenerator(orders_service_graph)
    req = DocRequest(
        repo_id="orders_app",
        target="src/services/order_service.py",
        doc_type="module"
    )
    res = generator.generate(req)

    assert res.doc_type == "module"
    assert "Module Documentation" in res.markdown_content
    assert "OrderService.create_order" in res.markdown_content
    assert len(res.symbols) >= 1


def test_generate_architecture_documentation(orders_service_graph):
    generator = RepoDocGenerator(orders_service_graph)
    req = DocRequest(repo_id="orders_app", doc_type="architecture")
    res = generator.generate(req)

    assert res.doc_type == "architecture"
    assert "Architecture Overview" in res.markdown_content
    assert res.diagram_mermaid is not None
    assert "flowchart TD" in res.diagram_mermaid
