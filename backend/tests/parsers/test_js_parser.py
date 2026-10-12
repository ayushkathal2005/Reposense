import pytest
from pathlib import Path
from parsers.javascript_parser import parse_js_file, JavaScriptParser

def test_parse_js_functions_and_classes(tmp_path):
    js_code = """
import { helper } from './utils';

/**
 * Service to manage sessions
 */
class SessionService extends BaseService {
  constructor() {
    super();
  }

  logout(userId) {
    helper(userId);
  }
}

function handleLogin(req) {
  const service = new SessionService();
  service.logout(req.id);
}

const formatUser = (user) => {
  return user.name;
};
"""
    file_path = tmp_path / "session.js"
    file_path.write_text(js_code)

    symbols = parse_js_file(file_path, "session.js")

    # Check import
    imports = [s for s in symbols if s.type == "import"]
    assert len(imports) == 1
    assert imports[0].name == "./utils"
    assert imports[0].language == "JavaScript"

    # Check class and heritage
    classes = [s for s in symbols if s.type == "class"]
    assert len(classes) == 1
    assert classes[0].name == "SessionService"
    assert "BaseService" in classes[0].dependencies
    assert classes[0].docstring == "Service to manage sessions"

    # Check method
    methods = [s for s in symbols if s.type == "method"]
    assert len(methods) == 2
    method_names = [m.name for m in methods]
    assert "SessionService.logout" in method_names
    assert "SessionService.constructor" in method_names
    logout_m = next(m for m in methods if m.name == "SessionService.logout")
    assert "helper" in logout_m.calls

    # Check functions
    functions = [s for s in symbols if s.type == "function"]
    assert len(functions) == 2
    names = [f.name for f in functions]
    assert "handleLogin" in names
    assert "formatUser" in names

def test_javascript_parser_class_interface():
    parser = JavaScriptParser()
    assert parser.language_name == "JavaScript"
    assert ".js" in parser.supported_extensions
