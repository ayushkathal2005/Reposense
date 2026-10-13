import pytest
from unittest.mock import MagicMock
from pathlib import Path
import networkx as nx
from query.llm import LLMClient
from graph.builder import build_knowledge_graph
from parsers import parse_file

def test_gemini_retry_backoff_on_503(monkeypatch):
    client = LLMClient()
    mock_gemini = MagicMock()

    # Raise 503 transient error twice, succeed on 3rd attempt
    call_count = 0
    def mock_generate_content(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("503 Service Unavailable: High load")
        resp = MagicMock()
        resp.text = "Success on attempt 3"
        return resp

    mock_gemini.models.generate_content = mock_generate_content
    client.client = mock_gemini

    # Mock time.sleep to run quickly
    slept_durations = []
    monkeypatch.setattr("time.sleep", lambda s: slept_durations.append(s))

    result = client.generate("test prompt", max_retries=3)

    assert result == "Success on attempt 3"
    assert call_count == 3
    assert slept_durations == [2, 4]  # delays for attempt 1 and 2


def test_gemini_fails_gracefully_after_max_retries(monkeypatch):
    client = LLMClient()
    mock_gemini = MagicMock()
    mock_gemini.models.generate_content.side_effect = Exception("503 Service Unavailable: Persistent failure")
    client.client = mock_gemini

    monkeypatch.setattr("time.sleep", lambda s: None)

    result = client.generate("test prompt", max_retries=3)

    assert "Error generating response" in result
    assert "503" in result
    assert mock_gemini.models.generate_content.call_count == 4  # Initial + 3 retries


def test_empty_repository_graph_construction():
    # An empty repository should produce a clean, valid graph with only the root repo node and 0 edges
    graph = build_knowledge_graph([], repo_id="empty_repo")

    assert isinstance(graph, nx.DiGraph)
    assert "empty_repo" in graph
    assert graph.nodes["empty_repo"]["type"] == "repository"
    assert len(graph.edges) == 0



def test_malformed_syntax_resilience(tmp_path):
    # A corrupt file should not crash parse_file
    bad_file = tmp_path / "broken.py"
    bad_file.write_text("def broken_syntax(:\n   print 'unclosed'", encoding="utf-8")

    symbols = parse_file(bad_file, "broken.py")
    # Python AST handles syntax errors gracefully by returning empty or partial symbols
    assert isinstance(symbols, list)
