import time
import json
import sys
import urllib.request
import urllib.error

API_URL = "http://127.0.0.1:8000/api"
REPO_URL = "https://github.com/octocat/Hello-World" 

def main():
    print("Waiting for server to start...")
    for _ in range(30):
        try:
            with urllib.request.urlopen(f"{API_URL.replace('/api', '')}/") as res:
                break
        except Exception:
            time.sleep(2)
            
    print(f"Ingesting {REPO_URL}...")
    req = urllib.request.Request(
        f"{API_URL}/repos/ingest", 
        data=json.dumps({"url": REPO_URL}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode('utf-8'))
    except Exception as e:
        print(f"Failed to ingest: {e}")
        sys.exit(1)
        
    repo_id = data["repo_id"]
    print(f"Started ingestion, repo_id: {repo_id}")
    
    while True:
        try:
            with urllib.request.urlopen(f"{API_URL}/repos/{repo_id}/status") as res:
                status_data = json.loads(res.read().decode('utf-8'))
                status = status_data["status"]
                print(f"Status: {status}")
                if status in ["completed", "failed"]:
                    break
        except Exception as e:
            print(f"Status check failed: {e}")
        time.sleep(2)
        
    if status == "failed":
        print("Ingestion failed.")
        sys.exit(1)
        
    print("Ingestion complete. Running query...")
    query = "Where is the hello world printed?"
    
    q_req = urllib.request.Request(
        f"{API_URL}/query",
        data=json.dumps({"repo_id": repo_id, "query": query}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(q_req) as res:
            query_res = json.loads(res.read().decode('utf-8'))
            print("Query Results:")
            print(json.dumps(query_res, indent=2))
    except urllib.error.HTTPError as e:
        print(f"Query failed: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"Query failed: {e}")

if __name__ == "__main__":
    main()
