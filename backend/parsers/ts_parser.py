import tree_sitter_javascript as ts_js
import tree_sitter_typescript as ts_ts
from tree_sitter import Language, Parser
from pathlib import Path
from typing import List, Optional
from .models import Symbol

JS_LANGUAGE = Language(ts_js.language())
TS_LANGUAGE = Language(ts_ts.language_typescript())
TSX_LANGUAGE = Language(ts_ts.language_tsx())

def get_parser(extension: str) -> Parser:
    parser = Parser()
    if extension in (".js", ".jsx"):
        parser.language = JS_LANGUAGE
    elif extension == ".ts":
        parser.language = TS_LANGUAGE
    elif extension == ".tsx":
        parser.language = TSX_LANGUAGE
    else:
        parser.language = JS_LANGUAGE
    return parser

def parse_ts_file(file_path: Path, relative_path: str) -> List[Symbol]:
    try:
        content = file_path.read_bytes()
        parser = get_parser(file_path.suffix.lower())
        tree = parser.parse(content)
        
        symbols = []
        
        def walk(node, current_class=None):
            if node.type == 'import_statement':
                import_path = None
                for child in node.children:
                    if child.type == 'string':
                        import_path = child.text.decode('utf8').strip("'\"")
                        break
                if import_path:
                    symbols.append(Symbol(
                        type="import",
                        name=import_path,
                        file=relative_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        dependencies=[import_path]
                    ))
                    
            elif node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                name = name_node.text.decode('utf8') if name_node else "AnonymousClass"
                
                symbols.append(Symbol(
                    type="class",
                    name=name,
                    file=relative_path,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                ))
                
                for child in node.children:
                    walk(child, current_class=name)
                    
            elif node.type in ('function_declaration', 'arrow_function', 'method_definition'):
                name = "AnonymousFunction"
                if node.type == 'method_definition':
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        name = name_node.text.decode('utf8')
                    if current_class:
                        name = f"{current_class}.{name}"
                elif node.type == 'function_declaration':
                    name_node = node.child_by_field_name('name')
                    if name_node:
                        name = name_node.text.decode('utf8')
                elif node.type == 'arrow_function':
                    # Best effort for arrow functions (if assigned to a variable)
                    if node.parent and node.parent.type == 'variable_declarator':
                        name_node = node.parent.child_by_field_name('name')
                        if name_node:
                            name = name_node.text.decode('utf8')
                
                sym_type = "method" if current_class and node.type == 'method_definition' else "function"
                
                calls = set()
                def extract_calls(n):
                    if n.type == 'call_expression':
                        func_node = n.child_by_field_name('function')
                        if func_node:
                            if func_node.type == 'member_expression':
                                prop = func_node.child_by_field_name('property')
                                if prop:
                                    calls.add(prop.text.decode('utf8'))
                            elif func_node.type == 'identifier':
                                calls.add(func_node.text.decode('utf8'))
                    for c in n.children:
                        extract_calls(c)
                        
                body_node = node.child_by_field_name('body')
                if body_node:
                    extract_calls(body_node)
                
                symbols.append(Symbol(
                    type=sym_type,
                    name=name,
                    file=relative_path,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    calls=list(calls)
                ))
            
            else:
                for child in node.children:
                    walk(child, current_class)

        walk(tree.root_node)
        return symbols
    except Exception as e:
        print(f"Error parsing JS/TS file {relative_path}: {e}")
        return []
