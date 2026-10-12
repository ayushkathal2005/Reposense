import pytest
from pathlib import Path
from parsers import parse_file

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

def test_python_fixture_extraction():
    auth_py = FIXTURES_DIR / "simple_python_app" / "auth.py"
    assert auth_py.exists()

    symbols = parse_file(auth_py, "auth.py")
    assert len(symbols) >= 3

    # Check class
    classes = [s for s in symbols if s.type == "class"]
    assert any(c.name == "AuthService" for c in classes)

    # Check method
    methods = [s for s in symbols if s.type == "method"]
    assert any(m.name == "AuthService.login" and "hash_password" in m.calls for m in methods)

    # Check function
    functions = [s for s in symbols if s.type == "function"]
    assert any(f.name == "hash_password" for f in functions)

def test_javascript_fixture_extraction():
    user_js = FIXTURES_DIR / "simple_node_app" / "user.js"
    assert user_js.exists()

    symbols = parse_file(user_js, "user.js")
    assert len(symbols) >= 4

    # Check imports
    imports = [s for s in symbols if s.type == "import"]
    assert len(imports) == 1
    assert imports[0].name == "./logger.js"
    assert imports[0].language == "JavaScript"

    # Check class & inheritance
    classes = [s for s in symbols if s.type == "class"]
    user_cls = next((c for c in classes if c.name == "User"), None)
    assert user_cls is not None
    assert "BaseEntity" in user_cls.dependencies
    assert "Represents a user account" in (user_cls.docstring or "")

    # Check method with calls
    methods = [s for s in symbols if s.type == "method"]
    save_method = next((m for m in methods if m.name == "User.save"), None)
    assert save_method is not None
    assert "logInfo" in save_method.calls

def test_typescript_fixture_extraction():
    service_ts = FIXTURES_DIR / "simple_typescript_app" / "service.ts"
    assert service_ts.exists()

    symbols = parse_file(service_ts, "service.ts")
    assert len(symbols) >= 5

    # Check interface
    interfaces = [s for s in symbols if s.type == "interface"]
    assert any(i.name == "PaymentConfig" for i in interfaces)

    # Check type
    types = [s for s in symbols if s.type == "type"]
    assert any(t.name == "TransactionStatus" for t in types)

    # Check class
    classes = [s for s in symbols if s.type == "class"]
    payment_cls = next((c for c in classes if c.name == "PaymentService"), None)
    assert payment_cls is not None
    assert "Handles payment transactions" in (payment_cls.docstring or "")

    # Check methods & calls
    methods = [s for s in symbols if s.type == "method"]
    proc_method = next((m for m in methods if m.name == "PaymentService.processPayment"), None)
    assert proc_method is not None
    assert "validate" in proc_method.calls

    # Check arrow function
    functions = [s for s in symbols if s.type == "function"]
    assert any(f.name == "executeOrder" for f in functions)

def test_structural_extraction_accuracy():
    """
    Controlled benchmark:
    Verified targets across 3 fixtures = 12 core constructs.
    Accuracy must be >= 90%.
    """
    total_expected = 12
    found_count = 0

    # 1. Python targets (3)
    py_syms = parse_file(FIXTURES_DIR / "simple_python_app" / "auth.py", "auth.py")
    if any(s.name == "AuthService" and s.type == "class" for s in py_syms):
        found_count += 1
    if any(s.name == "AuthService.login" and s.type == "method" for s in py_syms):
        found_count += 1
    if any(s.name == "hash_password" and s.type == "function" for s in py_syms):
        found_count += 1

    # 2. JavaScript targets (4)
    js_syms = parse_file(FIXTURES_DIR / "simple_node_app" / "user.js", "user.js")
    if any(s.name == "./logger.js" and s.type == "import" for s in js_syms):
        found_count += 1
    if any(s.name == "User" and s.type == "class" and "BaseEntity" in s.dependencies for s in js_syms):
        found_count += 1
    if any(s.name == "User.save" and "logInfo" in s.calls for s in js_syms):
        found_count += 1
    if any(s.name == "createUser" and s.type == "function" for s in js_syms):
        found_count += 1

    # 3. TypeScript targets (5)
    ts_syms = parse_file(FIXTURES_DIR / "simple_typescript_app" / "service.ts", "service.ts")
    if any(s.name == "PaymentConfig" and s.type == "interface" for s in ts_syms):
        found_count += 1
    if any(s.name == "TransactionStatus" and s.type == "type" for s in ts_syms):
        found_count += 1
    if any(s.name == "PaymentService" and s.type == "class" for s in ts_syms):
        found_count += 1
    if any(s.name == "PaymentService.processPayment" and "validate" in s.calls for s in ts_syms):
        found_count += 1
    if any(s.name == "executeOrder" and s.type == "function" for s in ts_syms):
        found_count += 1

    accuracy = found_count / total_expected
    assert accuracy >= 0.90, f"Accuracy {accuracy:.2f} is below 90% threshold"
    assert accuracy == 1.0, f"Expected 100% on controlled sample, got {accuracy:.2f}"
