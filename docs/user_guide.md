# RepoSense User Guide

Welcome to **RepoSense**, the intelligent repository intelligence pipeline that understands your codebase through Graph-based Vector Retrieval!

## Getting Started

RepoSense allows you to query any GitHub repository semantically. It clones the repository, parses the symbols (functions, classes, dependencies), generates NLP embeddings for these symbols, and connects them into a semantic Knowledge Graph.

### 1. Launching the App

If you are using Docker, simply run:
```bash
docker-compose up -d
```
The FastAPI backend will start on `http://localhost:8000` and the Web Dashboard will be available at `http://localhost:8080`.

### 2. Ingesting a Repository

1. Open your browser and navigate to `http://localhost:8080`.
2. In the "Connect Repository" section, paste a valid public GitHub URL (e.g., `https://github.com/tiangolo/fastapi`).
3. Click **Ingest Codebase**.
4. The system will clone, parse, and embed the repository in the background. Depending on the size of the repository, this can take a few minutes. Wait for the status to show "Ingestion Complete!".

### 3. Querying the Codebase

Once ingestion is complete, the Query interface will dynamically appear.
1. Type a natural language question about the repository (e.g., "How is the authentication token verified?").
2. Click **Ask RepoSense**.
3. RepoSense will search its Vector space to find the most relevant code blocks, and expand its search by querying the connected Knowledge Graph for dependencies and callers.
4. The synthesized response will be displayed alongside interactive badges referencing exactly which files and lines the information was drawn from. You can also view the exact prompt constructed for the LLM!

## Features

- **Vector Search**: Semantic search over code blocks using `sentence-transformers`.
- **Knowledge Graph**: Call graphs and dependency maps constructed automatically using `NetworkX`.
- **Intelligent Prompt Compiler**: Synthesizes the vector and graph contexts to instruct the LLM.
- **Glassmorphism UI**: A stunning dark-mode web dashboard.
