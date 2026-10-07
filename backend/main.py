from fastapi import FastAPI

app = FastAPI(title="RepoSense API")

@app.get("/")
def read_root():
    return {"message": "RepoSense API is running"}
