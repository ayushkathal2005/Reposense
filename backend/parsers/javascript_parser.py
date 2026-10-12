import tree_sitter_javascript as ts_js
from tree_sitter import Language, Parser
from pathlib import Path
from typing import List, Optional, Set
from .models import Symbol
from .base import BaseParser

JS_LANGUAGE = Language(ts_js.language())

def get_docstring(node) -> Optional[str]:
    """Extract leading comment or JSDoc if present immediately before node or its export parent."""
    comment_node = None
    if node.prev_sibling and node.prev_sibling.type == 'comment':
        comment_node = node.prev_sibling
    elif node.parent and node.parent.type == 'export_statement' and node.parent.prev_sibling:
        if node.parent.prev_sibling.type == 'comment':
            comment_node = node.parent.prev_sibling

    if comment_node:
        raw = comment_node.text.decode('utf-8')
        lines = []
        for line in raw.split('\n'):
            cleaned = line.strip().lstrip('/*').rstrip('*/').strip().lstrip('*').strip()
            if cleaned:
                lines.append(cleaned)
        return " ".join(lines) if lines else None
    return None

def extract_calls(node) -> List[str]:
    calls: Set[str] = set()
    def walk(n):
        if n.type == 'call_expression':
            func_node = n.child_by_field_name('function')
            if func_node:
                if func_node.type == 'member_expression':
                    prop = func_node.child_by_field_name('property')
                    if prop:
                        calls.add(prop.text.decode('utf-8'))
                elif func_node.type == 'identifier':
                    calls.add(func_node.text.decode('utf-8'))
        for c in n.children:
            walk(c)
    walk(node)
    return list(calls)

def extract_class_heritage(node) -> List[str]:
    dependencies: List[str] = []
    for child in node.children:
        if child.type == 'class_heritage':
            for h in child.children:
                if h.type in ('identifier', 'type_identifier', 'member_expression'):
                    dependencies.append(h.text.decode('utf-8'))
                elif h.type == 'extends_clause':
                    for sub in h.children:
                        if sub.type in ('identifier', 'type_identifier', 'member_expression'):
                            dependencies.append(sub.text.decode('utf-8'))
    return dependencies

def parse_js_file(file_path: Path, relative_path: str) -> List[Symbol]:
    try:
        content = file_path.read_bytes()
        parser = Parser()
        parser.language = JS_LANGUAGE
        tree = parser.parse(content)

        symbols: List[Symbol] = []

        def walk(node, current_class=None):
            if node.type == 'import_statement':
                import_path = None
                for child in node.children:
                    if child.type == 'string':
                        import_path = child.text.decode('utf-8').strip("'\"")
                        break
                if import_path:
                    symbols.append(Symbol(
                        type="import",
                        name=import_path,
                        file=relative_path,
                        language="JavaScript",
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        dependencies=[import_path]
                    ))

            elif node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                name = name_node.text.decode('utf-8') if name_node else "AnonymousClass"
                heritage = extract_class_heritage(node)
                doc = get_docstring(node)

                symbols.append(Symbol(
                    type="class",
                    name=name,
                    file=relative_path,
                    language="JavaScript",
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    dependencies=heritage,
                    docstring=doc
                ))

                for child in node.children:
                    walk(child, current_class=name)

            elif node.type in ('function_declaration', 'arrow_function', 'method_definition'):
                name = "AnonymousFunction"
                if node.type == 'method_definition':
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        name = name_node.text.decode('utf-8')
                    if current_class:
                        name = f"{current_class}.{name}"
                elif node.type == 'function_declaration':
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        name = name_node.text.decode('utf-8')
                elif node.type == 'arrow_function':
                    if node.parent and node.parent.type == 'variable_declarator':
                        name_node = node.parent.child_by_field_name('name')
                        if name_node:
                            name = name_node.text.decode('utf-8')

                sym_type = "method" if current_class and node.type == 'method_definition' else "function"
                body_node = node.child_by_field_name('body')
                calls = extract_calls(body_node) if body_node else []
                doc = get_docstring(node)

                symbols.append(Symbol(
                    type=sym_type,
                    name=name,
                    file=relative_path,
                    language="JavaScript",
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    calls=calls,
                    docstring=doc
                ))

            else:
                for child in node.children:
                    walk(child, current_class)

        walk(tree.root_node)
        return symbols
    except Exception as e:
        print(f"Error parsing JavaScript file {relative_path}: {e}")
        return []

class JavaScriptParser(BaseParser):
    @property
    def language_name(self) -> str:
        return "JavaScript"

    @property
    def supported_extensions(self) -> List[str]:
        return [".js", ".jsx", ".mjs", ".cjs"]

    def parse(self, file_path: Path, relative_path: str) -> List[Symbol]:
        return parse_js_file(file_path, relative_path)
