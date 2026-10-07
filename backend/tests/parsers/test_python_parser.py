import pytest
from pathlib import Path
from parsers.python_parser import parse_python_file

def test_parse_python_functions_and_classes(tmp_path):
    py_code = """
import os
from math import sqrt
from fastapi import FastAPI

app = FastAPI()

class Calculator:
    \"\"\"A simple calculator\"\"\"
    def __init__(self):
        self.value = 0
        
    @app.get("/add")
    def add(self, a, b):
        self.value = a + b
        return self.value
        
def main():
    calc = Calculator()
    print(calc.add(2, 3))
"""
    file_path = tmp_path / "test.py"
    file_path.write_text(py_code)
    
    symbols = parse_python_file(file_path, "test.py")
    
    imports = [s for s in symbols if s.type == "import"]
    assert len(imports) == 3
    assert imports[0].name == "os"
    assert imports[1].name == "math.sqrt"
    
    classes = [s for s in symbols if s.type == "class"]
    assert len(classes) == 1
    assert classes[0].name == "Calculator"
    assert classes[0].docstring == "A simple calculator"
    
    routes = [s for s in symbols if s.type == "route"]
    assert len(routes) == 1
    assert routes[0].name == "Calculator.add"
    assert routes[0].route_path == "/add"
    assert routes[0].route_method == "GET"
    
    functions = [s for s in symbols if s.type == "function"]
    assert len(functions) == 1
    assert functions[0].name == "main"
    assert "Calculator" in functions[0].calls
    assert "print" in functions[0].calls
    assert "add" in functions[0].calls
