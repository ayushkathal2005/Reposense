import pytest
from pathlib import Path
import networkx as nx
from evaluation.metrics.scorer import BenchmarkScorer
from evaluation.runners.benchmark_runner import BenchmarkRunner
from parsers.models import Symbol
from graph.builder import build_knowledge_graph

@pytest.fixture
def ecommerce_eval_graph():
    symbols = [
        Symbol(
            type="route",
            name="create_order_endpoint",
            file="api/routes.py",
            start_line=10,
            end_line=20,
            route_path="/api/orders",
            route_method="POST",
            calls=["OrderController.create"]
        ),
        Symbol(
            type="method",
            name="OrderController.create",
            file="controllers/order.py",
            start_line=25,
            end_line=45,
            calls=["OrderService.process_order"]
        ),
        Symbol(
            type="method",
            name="OrderService.process_order",
            file="services/order.py",
            start_line=50,
            end_line=85,
            calls=["PaymentGateway.charge", "OrderRepository.save"]
        ),
        Symbol(
            type="method",
            name="PaymentGateway.charge",
            file="gateways/payment.py",
            start_line=15,
            end_line=35,
            calls=["HttpStripeClient.post"]
        ),
        Symbol(
            type="method",
            name="OrderRepository.save",
            file="repositories/order.py",
            start_line=40,
            end_line=60,
            calls=[]
        ),
        Symbol(
            type="function",
            name="login",
            file="auth.py",
            start_line=1,
            end_line=20,
            calls=["verify_password"]
        ),
        Symbol(
            type="function",
            name="verify_password",
            file="auth.py",
            start_line=21,
            end_line=30
        ),
        Symbol(
            type="class",
            name="OrderRepository",
            file="repositories/order.py",
            start_line=1,
            end_line=100
        )
    ]
    return build_knowledge_graph(symbols, repo_id="ecommerce_eval")


def test_benchmark_dataset_integrity():
    dataset_path = Path(__file__).parent.parent.parent / "evaluation" / "datasets" / "benchmark_30.json"
    assert dataset_path.exists(), "benchmark_30.json must exist"

    runner = BenchmarkRunner(nx.DiGraph(), dataset_path=dataset_path)
    data = runner.load_dataset()

    assert len(data) >= 30, f"Expected at least 30 benchmark questions, got {len(data)}"

    categories = {item["category"] for item in data}
    expected_categories = {
        "symbol_lookup",
        "file_lookup",
        "dependency_questions",
        "execution_flow",
        "architecture",
        "impact_analysis",
        "debugging",
        "documentation"
    }
    for cat in expected_categories:
        assert cat in categories, f"Missing required category: {cat}"


def test_benchmark_scorer_metrics():
    # 1. Recall@5
    recall = BenchmarkScorer.calculate_recall_at_k(
        retrieved_items=["login", "auth.py", "UserController", "verify_password"],
        ground_truth_items=["login", "verify_password"],
        k=5
    )
    assert recall == 1.0

    # 2. Evidence Correctness
    ev_score = BenchmarkScorer.calculate_evidence_correctness(
        retrieved_evidence=[
            {"file": "src/auth.py"},
            {"file": "src/other.py"}
        ],
        expected_files=["src/auth.py"]
    )
    assert ev_score == 0.5

    # 3. Path Accuracy
    path_acc = BenchmarkScorer.calculate_path_accuracy(
        predicted_path=["create_order_endpoint", "OrderController.create", "OrderService.process_order", "OrderRepository.save"],
        expected_path=["create_order_endpoint", "OrderController.create", "OrderService.process_order"]
    )
    assert path_acc == 1.0

    # 4. Citation Correctness
    cit_score = BenchmarkScorer.calculate_citation_correctness(
        citations=["src/auth.py:10-20", "invalid/file.py:5"],
        valid_files={"src/auth.py"}
    )
    assert cit_score == 0.5

    # 5. Hallucination Rate
    hallucination_rate = BenchmarkScorer.calculate_hallucination_rate(
        referenced_symbols=["login", "FakeMagicService"],
        known_graph_symbols={"login", "verify_password"}
    )
    assert hallucination_rate == 0.5


def test_benchmark_runner_execution(ecommerce_eval_graph, tmp_path):
    runner = BenchmarkRunner(ecommerce_eval_graph, report_dir=tmp_path)
    report = runner.run_all()

    assert report["total_questions"] >= 30
    assert report["passed_questions"] >= 25
    assert report["overall_accuracy"] >= 0.80
    assert "metrics" in report
    assert report["metrics"]["hallucination_rate"] == 0.0

    report_file = tmp_path / "benchmark_report.json"
    assert report_file.exists()
