import pytest
import networkx as nx
from impact.analyzer import ChangeImpactAnalyzer
from impact.models import ImpactAnalysisResponse, DependentItem
from parsers.models import Symbol
from graph.builder import build_knowledge_graph

@pytest.fixture
def payment_pipeline_graph():
    """
    Creates a realistic multi-tier system graph:
    API Endpoint (api/order_routes.py)
      -> OrderController.checkout (controllers/order_controller.py)
        -> OrderService.place_order (services/order_service.py)
          -> PaymentService.process_payment (services/payment_service.py)
            -> StripeGateway.charge (gateways/stripe_gateway.py)

    Also test runner:
      test_process_payment (tests/test_payment.py)
        -> PaymentService.process_payment
    """
    symbols = [
        Symbol(
            type="route",
            name="checkout_endpoint",
            file="api/order_routes.py",
            start_line=15,
            end_line=30,
            route_path="/api/checkout",
            route_method="POST",
            calls=["OrderController.checkout"]
        ),
        Symbol(
            type="method",
            name="OrderController.checkout",
            file="controllers/order_controller.py",
            start_line=20,
            end_line=50,
            calls=["OrderService.place_order"]
        ),
        Symbol(
            type="method",
            name="OrderService.place_order",
            file="services/order_service.py",
            start_line=10,
            end_line=60,
            calls=["PaymentService.process_payment", "OrderRepository.save"]
        ),
        Symbol(
            type="method",
            name="PaymentService.process_payment",
            file="services/payment_service.py",
            start_line=100,
            end_line=150,
            calls=["StripeGateway.charge"]
        ),
        Symbol(
            type="method",
            name="StripeGateway.charge",
            file="gateways/stripe_gateway.py",
            start_line=12,
            end_line=45,
            calls=[]
        ),
        Symbol(
            type="method",
            name="OrderRepository.save",
            file="repositories/order_repo.py",
            start_line=5,
            end_line=25,
            calls=[]
        ),
        Symbol(
            type="function",
            name="test_process_payment",
            file="tests/test_payment.py",
            start_line=1,
            end_line=20,
            calls=["PaymentService.process_payment"]
        )
    ]
    return build_knowledge_graph(symbols, repo_id="payment_pipeline")


def test_unknown_symbol_returns_low_risk(payment_pipeline_graph):
    analyzer = ChangeImpactAnalyzer(payment_pipeline_graph)
    result = analyzer.analyze("NonExistentService.unknown_method")

    assert isinstance(result, ImpactAnalysisResponse)
    assert result.risk_level == "LOW"
    assert result.risk_score == 0.0
    assert result.blast_radius_count == 0
    assert "not found" in result.risk_factors[0].lower()


def test_process_payment_impact_traversal(payment_pipeline_graph):
    analyzer = ChangeImpactAnalyzer(payment_pipeline_graph)
    result = analyzer.analyze("PaymentService.process_payment")

    assert result.target_symbol == "PaymentService.process_payment"
    assert result.blast_radius_count >= 3

    # Direct callers should be OrderService.place_order and test_process_payment
    direct_symbols = {d.symbol for d in result.direct_dependents}
    assert "OrderService.place_order" in direct_symbols
    assert "test_process_payment" in direct_symbols

    # Indirect callers should include OrderController.checkout and checkout_endpoint
    indirect_symbols = {d.symbol for d in result.indirect_dependents}
    assert "OrderController.checkout" in indirect_symbols
    assert "checkout_endpoint" in indirect_symbols

    # Affected APIs and tests
    assert "checkout_endpoint" in result.affected_apis
    assert "test_process_payment" in result.affected_tests

    # Affected files
    assert "services/payment_service.py" in result.affected_files
    assert "services/order_service.py" in result.affected_files
    assert "controllers/order_controller.py" in result.affected_files
    assert "api/order_routes.py" in result.affected_files
    assert "tests/test_payment.py" in result.affected_files


def test_risk_level_critical_when_public_api_and_many_files(payment_pipeline_graph):
    analyzer = ChangeImpactAnalyzer(payment_pipeline_graph)
    result = analyzer.analyze("PaymentService.process_payment")

    # Has public API impact and affected files >= 3
    assert result.risk_level in ("HIGH", "CRITICAL")
    assert result.risk_score >= 7.0
    assert any("API" in factor for factor in result.risk_factors)


def test_leaf_symbol_isolated_low_risk(payment_pipeline_graph):
    # checkout_endpoint is the entrypoint - nothing calls it
    analyzer = ChangeImpactAnalyzer(payment_pipeline_graph)
    result = analyzer.analyze("checkout_endpoint")

    assert result.target_symbol == "checkout_endpoint"
    assert len(result.direct_dependents) == 0
    assert len(result.indirect_dependents) == 0
    assert result.blast_radius_count == 0
    assert result.risk_level == "LOW"


def test_explanation_contains_evidence(payment_pipeline_graph):
    analyzer = ChangeImpactAnalyzer(payment_pipeline_graph)
    result = analyzer.analyze("PaymentService.process_payment", explain=True)

    assert result.explanation is not None
    assert "PaymentService.process_payment" in result.explanation
    assert "Direct Callers" in result.explanation
    assert "OrderService.place_order" in result.explanation
