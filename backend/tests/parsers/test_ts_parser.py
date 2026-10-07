import pytest
from pathlib import Path
from parsers.ts_parser import parse_ts_file

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
