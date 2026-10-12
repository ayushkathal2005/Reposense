import ast
from pathlib import Path
from typing import List
from .models import Symbol
from .base import BaseParser

class PythonCodeVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.symbols: List[Symbol] = []
        self.current_class = None

    def visit_Import(self, node):
        for alias in node.names:
            self.symbols.append(Symbol(
                type="import",
                name=alias.name,
                file=self.file_path,
                language="Python",
                start_line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                dependencies=[alias.name]
            ))
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            for alias in node.names:
                name = f"{node.module}.{alias.name}"
                self.symbols.append(Symbol(
                    type="import",
                    name=name,
                    file=self.file_path,
                    language="Python",
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    dependencies=[node.module]
                ))
        self.generic_visit(node)

    def _extract_calls(self, node):
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
        return list(set(calls))
        
    def _extract_decorators(self, node):
        decorators = []
        route_path = None
        route_method = None
        
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    decorators.append(dec.func.id)
                elif isinstance(dec.func, ast.Attribute):
                    decorators.append(dec.func.attr)
                    
                    if dec.func.attr in ("get", "post", "put", "delete", "patch"):
                        route_method = dec.func.attr.upper()
                        if dec.args and isinstance(dec.args[0], ast.Constant):
                            route_path = str(dec.args[0].value)
        
        return decorators, route_path, route_method

    def visit_ClassDef(self, node):
        calls = self._extract_calls(node)
        decorators, _, _ = self._extract_decorators(node)
        
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
                
        self.symbols.append(Symbol(
            type="class",
            name=node.name,
            file=self.file_path,
            language="Python",
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            calls=calls,
            dependencies=bases,
            decorators=decorators,
            docstring=ast.get_docstring(node)
        ))
        
        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node):
        self._handle_function(node)

    def visit_AsyncFunctionDef(self, node):
        self._handle_function(node)
        
    def _handle_function(self, node):
        calls = self._extract_calls(node)
        decorators, route_path, route_method = self._extract_decorators(node)
        
        sym_type = "method" if self.current_class else "function"
        name = f"{self.current_class}.{node.name}" if self.current_class else node.name
        
        if route_path:
            sym_type = "route"
            
        self.symbols.append(Symbol(
            type=sym_type,
            name=name,
            file=self.file_path,
            language="Python",
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            calls=calls,
            decorators=decorators,
            docstring=ast.get_docstring(node),
            route_path=route_path,
            route_method=route_method
        ))
        self.generic_visit(node)

def parse_python_file(file_path: Path, relative_path: str) -> List[Symbol]:
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
        visitor = PythonCodeVisitor(relative_path)
        visitor.visit(tree)
        return visitor.symbols
    except Exception as e:
        print(f"Error parsing python file {relative_path}: {e}")
        return []

class PythonParser(BaseParser):
    @property
    def language_name(self) -> str:
        return "Python"

    @property
    def supported_extensions(self) -> List[str]:
        return [".py"]

    def parse(self, file_path: Path, relative_path: str) -> List[Symbol]:
        return parse_python_file(file_path, relative_path)
