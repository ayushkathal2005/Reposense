import json
from pathlib import Path
from parsers import parse_file

def main():
    files = [
        Path("ingestion/detector.py"),
        Path("ingestion/git_client.py"),
        Path("ingestion/service.py"),
        Path("parsers/python_parser.py")
    ]
    
    count = 0
    for file in files:
        symbols = parse_file(file, str(file))
        functions = [s for s in symbols if s.type in ("function", "method", "route")]
        
        for f in functions:
            print(json.dumps(f.model_dump(), indent=2))
            count += 1
            if count >= 10:
                print(f"Total verified: {count}")
                return

if __name__ == "__main__":
    main()
