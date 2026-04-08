import os
import json
from datetime import datetime
from unittest.mock import MagicMock, patch
from core.research import (
    CACHE_FILE,
    get_research_context,
    read_frontmatter,
    render_research_report,
    search_arxiv,
)

def test_search_arxiv_mock(tmp_path, monkeypatch):
    """Verifies that search_arxiv correctly handles ArXiv results and caching."""
    monkeypatch.chdir(tmp_path)
    
    # Mock ArXiv client results
    mock_result = MagicMock()
    mock_result.title = "Test Paper"
    mock_result.summary = "This is a test summary about momentum."
    mock_result.pdf_url = "http://example.com/test.pdf"
    mock_result.published.strftime.return_value = "2023-01-01"
    
    mock_client = MagicMock()
    mock_client.results.return_value = [mock_result]
    
    with patch("arxiv.Client", return_value=mock_client):
        # First call: Search ArXiv
        results = search_arxiv("momentum trading")
        assert len(results) == 1
        assert results[0]["title"] == "Test Paper"
        
        # Verify cache file created
        assert os.path.exists(CACHE_FILE)
        
        # Second call: Should hit cache (we check this by verifying Client was called once)
        results2 = search_arxiv("momentum trading")
        assert len(results2) == 1
        assert mock_client.results.call_count == 1

def test_get_research_context():
    """Verifies that the context string is formatted correctly."""
    with patch("core.research.search_arxiv") as mock_search:
        mock_search.return_value = [{
            "title": "Title A",
            "summary": "Summary A",
            "url": "URL A",
            "published": "2023-01-01"
        }]
        
        context = get_research_context("test hypothesis")
        assert "PAPER: Title A" in context
        assert "SUMMARY: Summary A" in context
        assert "URL: URL A" in context

def test_local_bm25_search(tmp_path, monkeypatch):
    """Verifies that local BM25 ranking works correctly."""
    monkeypatch.chdir(tmp_path)
    
    # Setup a mock cache with multiple papers
    cache = {
        "query1": [
            {"title": "Deep Learning for Quant", "summary": "Neural networks in finance", "url": "url1", "published": "2023"},
            {"title": "Bollinger Bands", "summary": "Mean reversion indicators", "url": "url2", "published": "2022"}
        ],
        "query2": [
            {"title": "Momentum Trading", "summary": "Trend following strategies", "url": "url3", "published": "2021"}
        ]
    }
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)
        
    from core.research import local_bm25_search
    
    # Search for something that matches 'Neural'
    results = local_bm25_search("neural finance")
    assert len(results) > 0
    assert "Deep Learning" in results[0]["title"]
    
    # Search for 'Trend'
    results2 = local_bm25_search("trend following")
    assert len(results2) > 0
    assert "Momentum" in results2[0]["title"]


def test_render_research_report_supports_stdout_output():
    report, output_path, reused_existing = render_research_report(
        query="test hypothesis",
        papers=[],
        web_results=[],
        output="stdout",
        generated_at=datetime(2026, 4, 8, 8, 0, 0),
    )

    assert report.startswith("---\n")
    assert output_path is None
    assert reused_existing is False
    assert "No specific academic papers found" in report


def test_read_frontmatter_returns_query(tmp_path):
    note_path = tmp_path / "note.md"
    note_path.write_text(
        "---\n"
        "note_type: research\n"
        "query: mean reversion setup\n"
        "---\n\n"
        "# Research\n"
    )

    frontmatter = read_frontmatter(note_path)

    assert frontmatter["query"] == "mean reversion setup"
