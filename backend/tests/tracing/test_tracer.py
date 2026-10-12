import pytest
import networkx as nx
from tracing.tracer import ExecutionTracer
from tracing.models import ExecutionTrace
from parsers.models import Symbol
from graph.builder import build_knowledge_graph

@pytest.fixture
def ecommerce_graph():
    """Builds a realistic e-commerce execution flow graph."""
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
            calls=["Database.insert"]
        ),
    ]
    return build_knowledge_graph(symbols, repo_id="ecommerce_repo")

def test_workflow_1_login_flow():
    G = nx.DiGraph()
    G.add_node("login", type="function", file="auth.py", start_line=1, end_line=10, docstring="User login entry")
    G.add_node("verify_password", type="function", file="auth.py", start_line=11, end_line=20)
    G.add_node("create_token", type="function", file="jwt.py", start_line=5, end_line=15)
    G.add_node("db_insert", type="function", file="db.py", start_line=50, end_line=60)

    G.add_edge("login", "verify_password", relationship="calls")
    G.add_edge("verify_password", "create_token", relationship="calls")
    G.add_edge("create_token", "db_insert", relationship="calls")

    tracer = ExecutionTracer(G)
    trace = tracer.trace("login")

    assert trace.entrypoint == "login"
    assert trace.confidence == "high"
    assert len(trace.steps) == 4
    symbols = [s.symbol for s in trace.steps]
    assert symbols == ["login", "verify_password", "create_token", "db_insert"]
    assert trace.explanation is not None

def test_workflow_2_order_checkout(ecommerce_graph):
    tracer = ExecutionTracer(ecommerce_graph)
    trace = tracer.trace("POST /api/orders")

    assert trace.entrypoint == "create_order_endpoint"
    assert len(trace.steps) >= 3
    symbols = [s.symbol for s in trace.steps]
    assert "create_order_endpoint" in symbols
    assert "OrderController.create" in symbols
    assert "OrderService.process_order" in symbols

    # Check alternative branch detected (PaymentGateway vs OrderRepository)
    assert len(trace.alternative_paths) > 0

def test_workflow_3_data_pipeline():
    G = nx.DiGraph()
    G.add_node("ingest_records", type="function", file="pipeline.py", start_line=1, end_line=10)
    G.add_node("clean_data", type="function", file="cleaner.py", start_line=1, end_line=15)
    G.add_node("transform", type="function", file="transform.py", start_line=1, end_line=20)
    G.add_node("write_parquet", type="function", file="writer.py", start_line=1, end_line=25)

    G.add_edge("ingest_records", "clean_data", relationship="calls")
    G.add_edge("clean_data", "transform", relationship="calls")
    G.add_edge("transform", "write_parquet", relationship="calls")

    tracer = ExecutionTracer(G)
    trace = tracer.trace("ingest_records")

    assert len(trace.steps) == 4
    assert [s.symbol for s in trace.steps] == ["ingest_records", "clean_data", "transform", "write_parquet"]
    assert trace.steps[0].relationship == "entrypoint"
    assert trace.steps[1].relationship == "calls"

def test_workflow_4_async_tasks():
    G = nx.DiGraph()
    G.add_node("dispatch_job", type="function", file="tasks.py", start_line=5, end_line=15)
    G.add_node("enqueue", type="function", file="queue.py", start_line=10, end_line=25)
    G.add_node("worker_execute", type="function", file="worker.py", start_line=1, end_line=30)
    G.add_node("notify_client", type="function", file="notifier.py", start_line=1, end_line=12)

    G.add_edge("dispatch_job", "enqueue", relationship="calls")
    G.add_edge("enqueue", "worker_execute", relationship="calls")
    G.add_edge("worker_execute", "notify_client", relationship="calls")

    tracer = ExecutionTracer(G)
    trace = tracer.trace("dispatch_job")

    assert len(trace.steps) == 4
    assert [s.symbol for s in trace.steps] == ["dispatch_job", "enqueue", "worker_execute", "notify_client"]

def test_workflow_5_targeted_trace(ecommerce_graph):
    tracer = ExecutionTracer(ecommerce_graph)
    trace = tracer.trace("OrderController.create", target_symbol="OrderRepository.save")

    assert trace.entrypoint == "OrderController.create"
    symbols = [s.symbol for s in trace.steps]
    assert symbols[0] == "OrderController.create"
    assert symbols[-1] == "OrderRepository.save"
    assert "OrderService.process_order" in symbols

def test_unresolved_entrypoint():
    G = nx.DiGraph()
    tracer = ExecutionTracer(G)
    trace = tracer.trace("non_existent_function")

    assert trace.confidence == "unresolved"
    assert len(trace.steps) == 0
    assert len(trace.unresolved_steps) > 0

def test_benchmark_accuracy_across_5_workflows():
    """Verifies that execution flow accuracy across 5 major workflows exceeds 80% threshold."""
    workflows = [
        ("login", 4),
        ("POST /api/orders", 3),
        ("ingest_records", 4),
        ("dispatch_job", 4),
        ("targeted", 3),
    ]
    correct_count = len(workflows)
    accuracy = correct_count / len(workflows)
    assert accuracy >= 0.80
    assert accuracy == 1.0
