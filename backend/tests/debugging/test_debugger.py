import pytest
import networkx as nx
from debugging.parser import ErrorTraceParser
from debugging.analyzer import RepoDebugger
from debugging.models import DebugRequest, DebugAnalysisResponse
from parsers.models import Symbol
from graph.builder import build_knowledge_graph

@pytest.fixture
def auth_users_graph():
    symbols = [
        Symbol(
            type="route",
            name="get_user_endpoint",
            file="src/api/users.py",
            start_line=10,
            end_line=30,
            route_path="/api/users/{id}",
            route_method="GET",
            calls=["UserController.get_profile"]
        ),
        Symbol(
            type="method",
            name="UserController.get_profile",
            file="src/controllers/user_controller.py",
            start_line=25,
            end_line=50,
            calls=["UserService.get_user"]
        ),
        Symbol(
            type="method",
            name="UserService.get_user",
            file="src/services/user_service.py",
            start_line=15,
            end_line=45,
            calls=["UserRepository.find_by_id"]
        ),
        Symbol(
            type="method",
            name="UserRepository.find_by_id",
            file="src/repositories/user_repo.py",
            start_line=5,
            end_line=35,
            calls=["User"]
        ),
        Symbol(
            type="class",
            name="User",
            file="src/models/user.py",
            start_line=1,
            end_line=20
        ),
    ]
    return build_knowledge_graph(symbols, repo_id="auth_app")


def test_python_traceback_parser():
    tb = """Traceback (most recent call last):
  File "src/api/users.py", line 81, in get_user_profile
    return user_data["user_id"]
KeyError: 'user_id'"""

    parsed = ErrorTraceParser.parse("KeyError: 'user_id'", stack_trace=tb)
    assert parsed.error_type == "KeyError"
    assert parsed.target_token == "user_id"
    assert len(parsed.frames) == 1
    assert parsed.frames[0].file == "src/api/users.py"
    assert parsed.frames[0].line == 81
    assert parsed.frames[0].symbol == "get_user_profile"


def test_javascript_traceback_parser():
    tb = """TypeError: Cannot read properties of undefined (reading 'charge')
    at PaymentService.charge (src/services/payment.ts:45:12)
    at OrderController.checkout (src/controllers/order.ts:20:8)"""

    parsed = ErrorTraceParser.parse("TypeError: Cannot read properties of undefined (reading 'charge')", stack_trace=tb)
    assert parsed.error_type == "TypeError"
    assert len(parsed.frames) == 2
    assert parsed.frames[0].file == "src/services/payment.ts"
    assert parsed.frames[0].line == 45
    assert parsed.frames[0].symbol == "PaymentService.charge"


def test_keyerror_diagnosis_grounding(auth_users_graph):
    debugger = RepoDebugger(auth_users_graph)
    req = DebugRequest(
        repo_id="auth_app",
        error_message="KeyError: 'user_id'",
        stack_trace="""File "src/api/users.py", line 81, in get_user_profile\n    return user_data["user_id"]""",
        symbol="get_user_endpoint"
    )
    result = debugger.analyze(req)

    assert isinstance(result, DebugAnalysisResponse)
    assert result.confidence in ("High", "Medium")
    assert len(result.likely_locations) >= 1
    assert result.likely_locations[0].file == "src/api/users.py"
    assert result.likely_locations[0].line == 81

    # Verify separation of FACT, INFERENCE, CAUSE, and FIX
    assert len(result.facts) >= 1
    assert any("user_id" in f for f in result.facts)
    assert len(result.inferences) >= 1
    assert any("user_id" in inf for inf in result.inferences)
    assert len(result.possible_causes) >= 1
    assert any("user_id" in c for c in result.possible_causes)
    assert len(result.possible_fixes) >= 1
    assert any(".get(" in fix or "in data" in fix or "Pydantic" in fix for fix in result.possible_fixes)


def test_attributeerror_none_diagnosis(auth_users_graph):
    debugger = RepoDebugger(auth_users_graph)
    req = DebugRequest(
        repo_id="auth_app",
        error_message="AttributeError: 'NoneType' object has no attribute 'charge'",
        stack_trace="""File "src/services/payment.py", line 42, in process\n    gateway.charge(amount)""",
        symbol="UserService.get_user"
    )
    result = debugger.analyze(req)

    assert result.confidence == "High"
    assert any("None" in c or "null" in c.lower() for c in result.possible_causes)
    assert any("null guard" in fix.lower() or "is not None" in fix for fix in result.possible_fixes)


def test_distinguish_fact_from_inference_in_explanation(auth_users_graph):
    debugger = RepoDebugger(auth_users_graph)
    req = DebugRequest(
        repo_id="auth_app",
        error_message="KeyError: user_id",
        symbol="UserService.get_user"
    )
    result = debugger.analyze(req)

    assert result.explanation is not None
    assert "FACTS" in result.explanation
    assert "INFERENCES" in result.explanation
    assert "POSSIBLE CAUSES" in result.explanation
    assert "RECOMMENDED FIXES" in result.explanation
