# RepoSense API Reference

The RepoSense backend exposes a REST API powered by FastAPI. 
Base URL: `http://localhost:8000/api`

---

## 1. `POST /repos/ingest`
Starts a background task to ingest a GitHub repository.

**Request Body (JSON):**
```json
{
  "url": "https://github.com/octocat/Hello-World"
}
```

**Response (JSON):**
Returns a dynamically generated Repository UUID immediately, while the ingestion happens in the background.
```json
{
  "message": "Ingestion started",
  "repo_id": "92d196ac-6e33-483c-b7d3-bb24de0f91d7"
}
```

---

## 2. `GET /repos/{repo_id}/status`
Poll this endpoint to track the background ingestion status.

**Path Parameters:**
- `repo_id`: The UUID returned by the `/ingest` endpoint.

**Response (JSON):**
```json
{
  "status": "processing" // Can be "processing", "completed", or "failed"
}
```

---

## 3. `POST /query`
Execute a semantic query against a fully ingested repository.

**Request Body (JSON):**
```json
{
  "repo_id": "92d196ac-6e33-483c-b7d3-bb24de0f91d7",
  "query": "Where is the hello world printed?"
}
```

**Response (JSON):**
```json
{
  "answer": "This is a synthesized answer from the LLM based on the context.",
  "sources": [
    {
      "name": "SessionManager",
      "file": "auth.py",
      "lines": "40-50"
    }
  ],
  "prompt": "User Query: ... \n\nPrimary Context: ... \n\nRelated Components: ..."
}
```
*Note: In the current version, the LLM is mocked for deterministic end-to-end integration testing.*
