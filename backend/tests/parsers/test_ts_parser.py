import pytest
from pathlib import Path
from parsers.typescript_parser import parse_ts_file, TypeScriptParser

def test_parse_ts_functions_and_classes(tmp_path):
    ts_code = """
import { useState } from 'react';

class Greeter {
    greet(name: string) {
        console.log("Hello", name);
    }
}

function main() {
    const g = new Greeter();
    g.greet("World");
}

const arrow = () => {
    alert("arrow");
};
"""
    file_path = tmp_path / "test.ts"
    file_path.write_text(ts_code)
    
    symbols = parse_ts_file(file_path, "test.ts")
    
    imports = [s for s in symbols if s.type == "import"]
    assert len(imports) == 1
    assert imports[0].name == "react"
    assert imports[0].language == "TypeScript"
    
    classes = [s for s in symbols if s.type == "class"]
    assert len(classes) == 1
    assert classes[0].name == "Greeter"
    
    methods = [s for s in symbols if s.type == "method"]
    assert len(methods) == 1
    assert methods[0].name == "Greeter.greet"
    assert "log" in methods[0].calls
    
    functions = [s for s in symbols if s.type == "function"]
    assert len(functions) == 2
    
    main_fn = next(f for f in functions if f.name == "main")
    assert "greet" in main_fn.calls
    
    arrow_fn = next(f for f in functions if f.name == "arrow")
    assert "alert" in arrow_fn.calls

def test_parse_ts_interfaces_types_and_heritage(tmp_path):
    ts_code = """
export interface UserPayload {
    id: string;
    email: string;
}

export type Role = 'admin' | 'user';

/**
 * Primary user repository implementation
 */
export class UserRepository extends BaseRepository {
    findUser(id: string) {
        dbQuery(id);
    }
}
"""
    file_path = tmp_path / "repo.ts"
    file_path.write_text(ts_code)

    symbols = parse_ts_file(file_path, "repo.ts")

    interfaces = [s for s in symbols if s.type == "interface"]
    assert len(interfaces) == 1
    assert interfaces[0].name == "UserPayload"

    types = [s for s in symbols if s.type == "type"]
    assert len(types) == 1
    assert types[0].name == "Role"

    classes = [s for s in symbols if s.type == "class"]
    assert len(classes) == 1
    assert classes[0].name == "UserRepository"
    assert "BaseRepository" in classes[0].dependencies
    assert classes[0].docstring == "Primary user repository implementation"

def test_typescript_parser_interface():
    parser = TypeScriptParser()
    assert parser.language_name == "TypeScript"
    assert ".ts" in parser.supported_extensions
    assert ".tsx" in parser.supported_extensions
