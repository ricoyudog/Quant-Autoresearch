import arxiv
import bm25s
from datetime import datetime
import json
import os
from pathlib import Path
import re
import requests
from typing import Any, Dict, List, Optional

import yaml

from config.vault import ensure_vault_directories, get_vault_paths

CACHE_FILE = "experiments/results/research_cache.json"
WEB_CACHE_FILE = "experiments/results/web_research_cache.json"
KNOWLEDGE_NOTES = {
    "overfit-defense.md": """---
note_type: knowledge
topic: overfit-defense
tags:
  - knowledge
  - overfitting
  - statistics
---

# Overfit Defense Reference

## Why Overfitting Happens
- repeated backtest iteration can turn noise into seemingly stable alpha
- significance and out-of-sample discipline matter more than headline Sharpe alone

## Built-in Defenses
- use walk-forward validation and baseline comparisons
- prefer statistically significant improvements
- treat drawdown and profit factor as first-class checks
""",
    "market-microstructure.md": """---
note_type: knowledge
topic: market-microstructure
tags:
  - knowledge
  - microstructure
  - liquidity
---

# Market Microstructure Notes

## Practical Reminders
- liquidity, spread, and participation matter as much as signal quality
- volume spikes can change slippage and execution behavior
- regime changes often appear in volatility and volume before price trends stabilize
""",
    "strategy-pattern-catalog.md": """---
note_type: knowledge
topic: strategy-pattern-catalog
tags:
  - knowledge
  - strategy-patterns
---

# Strategy Pattern Catalog

## Reference Patterns
- momentum
- mean reversion
- breakout
- regime-filtered combinations

Use these notes as prompts for new hypotheses, not as hard-coded strategy templates.
""",
    "experiment-methodology.md": """---
note_type: knowledge
topic: experiment-methodology
tags:
  - knowledge
  - experimentation
---

# Experiment Methodology

## Workflow
1. capture a falsifiable hypothesis
2. run the baseline before editing
3. keep only statistically stronger results
4. log findings in the vault and in `results.tsv`
""",
}

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def get_unique_papers():
    cache = load_cache()
    papers = []
    seen_urls = set()
    
    # Add papers from cache
    for query_results in cache.values():
        for p in query_results:
            if p["url"] not in seen_urls:
                papers.append(p)
                seen_urls.add(p["url"])
    
    # Add papers from local corpus
    corpus_file = "data/bm25_papers.json"
    if os.path.exists(corpus_file):
        with open(corpus_file, "r") as f:
            corpus_papers = json.load(f)
            for p in corpus_papers:
                if p["url"] not in seen_urls:
                    p["source"] = "local_corpus"
                    papers.append(p)
                    seen_urls.add(p["url"])
                    
    return papers

def load_web_cache():
    if os.path.exists(WEB_CACHE_FILE):
        with open(WEB_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_web_cache(cache):
    os.makedirs(os.path.dirname(WEB_CACHE_FILE), exist_ok=True)
    with open(WEB_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def search_web(query: str, num_results: int = 8) -> List[Dict[str, Any]]:
    """Search the web for current events, macroeconomic data, geopolitical analysis."""
    cache = load_web_cache()
    
    # Check cache first
    if query in cache:
        print(f"  [Web Search] Cache hit for: {query}")
        return cache[query]
    
    print(f"  [Web Search] Searching for: {query}...")
    
    # Try Exa API first (uses POST)
    exa_api_key = os.getenv("EXA_API_KEY")
    if exa_api_key:
        try:
            headers = {
                "Authorization": f"Bearer {exa_api_key}",
                "Content-Type": "application/json"
            }
            payload = {"query": query, "num_results": num_results}
            response = requests.post(
                "https://api.exa.ai/search",
                headers=headers,
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get("results", []):
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("snippet", "")[:500],
                        "published": item.get("published_date", ""),
                        "source": "exa"
                    })
                cache[query] = results
                save_web_cache(cache)
                return results
            else:
                print(f"  [Web Search] Exa API error: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"  [Web Search] Exa API error: {e}")
    
    # Try SerpAPI
    serpapi_key = os.getenv("SERPAPI_KEY")
    if serpapi_key:
        try:
            params = {"q": query, "num": num_results, "api_key": serpapi_key}
            response = requests.get("https://serpapi.com/search", params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get("organic_results", [])[:num_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", "")[:500],
                        "published": "",
                        "source": "serpapi"
                    })
                cache[query] = results
                save_web_cache(cache)
                return results
        except Exception as e:
            print(f"  [Web Search] SerpAPI error: {e}")
    
    # No API available
    return []

def fetch_url_content(url: str, max_chars: int = 10000) -> Dict[str, Any]:
    """Fetch and extract content from a specific URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; QuantAutoresearch/1.0)"}
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}"}
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(line for line in lines if line)
        
        if len(text) > max_chars:
            text = text[:max_chars] + "... [truncated]"
        
        return {
            "success": True,
            "url": url,
            "content": text,
            "content_length": len(text)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_comprehensive_research_context(
    hypothesis: str,
    max_papers: int = 3,
    max_web_results: int = 5,
    include_web: bool = True
) -> str:
    """Get both academic and web research context for a hypothesis.
    
    Args:
        hypothesis: The research hypothesis or question
        max_papers: Maximum ArXiv papers to return
        max_web_results: Maximum web results to return
        include_web: Whether to include web search results
        
    Returns:
        Formatted string with both academic and web research context
    """
    context = ""
    
    # Academic research (ArXiv)
    academic_context = get_research_context(hypothesis, max_papers=max_papers)
    context += academic_context + "\n"
    
    # Web research for current events / macroeconomic data
    if include_web:
        web_results = search_web(hypothesis, num_results=max_web_results)
        
        context += "\n--- Web Research Context ---\n"
        if not web_results:
            context += "No web results available. Configure EXA_API_KEY or SERPAPI_KEY in .env for web search.\n"
        else:
            for i, result in enumerate(web_results, 1):
                context += f"RESULT {i}: {result.get('title', 'N/A')}\n"
                context += f"URL: {result.get('url', 'N/A')}\n"
                context += f"SUMMARY: {result.get('snippet', 'N/A')}\n"
                if result.get('published'):
                    context += f"PUBLISHED: {result.get('published')}\n"
                context += "\n"
    
    return context

def local_bm25_search(query, top_n=3):
    """
    Search papers already in the cache using BM25.
    """
    papers = get_unique_papers()
    if not papers:
        return []
    
    # Simple tokenization
    def tokenize(text):
        return re.sub(r'[^a-zA-Z0-9\s]', '', text.lower()).split()

    corpus = [tokenize(f"{p['title']} {p['summary']}") for p in papers]
    
    try:
        retriever = bm25s.BM25(corpus=papers)
        retriever.index(corpus)
        
        query_tokens = tokenize(query)
        # BM25S expects a list of queries [ [tokens], [tokens] ]
        results, scores = retriever.retrieve([query_tokens], k=top_n)
        
        # Filter by a small threshold to ensure relevance
        relevant_papers = []
        for i in range(len(results[0])):
            if scores[0, i] > 0.5: # Threshold for BM25 score relevance
                relevant_papers.append(results[0, i])
        return relevant_papers
    except Exception as e:
        print(f"  [Research] BM25 Error: {e}")
        return []

def search_arxiv(query, max_results=5):
    """
    Searches ArXiv for papers matching the query and returns metadata.
    """
    # First, try local BM25
    local_results = local_bm25_search(query, top_n=max_results)
    if local_results:
        print(f"  [Research] Local BM25 hit: Found {len(local_results)} relevant papers.")
        return local_results

    # If nothing relevant locally, check exact query cache
    cache = load_cache()
    if query in cache:
        print(f"  [Research] Cache hit for: {query}")
        return cache[query]

    print(f"  [Research] Searching ArXiv for: {query}...")
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )

    results = []
    for result in client.results(search):
        results.append({
            "title": result.title,
            "summary": result.summary,
            "url": result.pdf_url,
            "published": result.published.strftime("%Y-%m-%d")
        })

    cache[query] = results
    save_cache(cache)
    return results

def get_research_context(hypothesis, max_papers=3):
    """
    High-level helper to get academic context for a given hypothesis.
    Uses BM25 to search locally before going to ArXiv.
    """
    # Clean query
    query = re.sub(r'[^a-zA-Z0-9\s]', '', hypothesis)
    papers = search_arxiv(query, max_results=max_papers)
    
    context = "\n--- Academic Research Context ---\n"
    if not papers:
        context += "No specific academic papers found for this hypothesis.\n"
    else:
        for p in papers:
            context += f"PAPER: {p['title']} ({p['published']})\n"
            context += f"SUMMARY: {p['summary'][:500]}...\n"
            context += f"URL: {p['url']}\n\n"
    
    return context


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    return slug.strip("-") or "research"


def titleize_query(query: str) -> str:
    return " ".join(word.capitalize() for word in query.split())


def build_research_frontmatter(
    query: str,
    depth: str,
    generated_at: datetime,
    sources_count: int,
) -> Dict[str, Any]:
    return {
        "note_type": "research",
        "research_type": "literature",
        "query": query,
        "date": generated_at.strftime("%Y-%m-%d"),
        "depth": depth,
        "sources_count": sources_count,
        "tags": ["research", depth],
    }


def format_research_report(
    query: str,
    papers: List[Dict[str, Any]],
    web_results: Optional[List[Dict[str, Any]]] = None,
    generated_at: Optional[datetime] = None,
    depth: str = "shallow",
) -> str:
    generated_at = generated_at or datetime.now()
    web_results = web_results or []
    frontmatter = build_research_frontmatter(
        query=query,
        depth=depth,
        generated_at=generated_at,
        sources_count=len(papers) + len(web_results),
    )
    frontmatter_text = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()

    lines = [
        "---",
        frontmatter_text,
        "---",
        "",
        f"# Research: {titleize_query(query)}",
        "",
        "## Academic Papers",
        "",
    ]

    if not papers:
        lines.append("No specific academic papers found for this hypothesis.")
        lines.append("")
    else:
        for index, paper in enumerate(papers, start=1):
            lines.extend(
                [
                    f"### Paper {index}: {paper.get('title', 'Untitled')}",
                    f"- **Source**: ArXiv",
                    f"- **URL**: {paper.get('url', 'N/A')}",
                    f"- **Published**: {paper.get('published', 'N/A')}",
                    f"- **Summary**: {paper.get('summary', 'N/A')}",
                    "",
                ]
            )

    if web_results:
        lines.extend(["## Web Resources", ""])
        for result in web_results:
            lines.extend(
                [
                    f"### [{result.get('title', 'Untitled')}]({result.get('url', '')})",
                    f"- **Source**: {result.get('source', 'web')}",
                    f"- **Snippet**: {result.get('snippet', 'N/A')}",
                    "",
                ]
            )

    return "\n".join(lines).rstrip() + "\n"


def read_frontmatter(note_path: str | Path) -> Dict[str, Any]:
    text = Path(note_path).read_text()
    if not text.startswith("---\n"):
        return {}

    _, frontmatter_block, _ = text.split("---", 2)
    parsed = yaml.safe_load(frontmatter_block) or {}
    return parsed if isinstance(parsed, dict) else {}


def _tokenize_query(query: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", query.lower()))


def find_existing_research_note(query: str, research_dir: str | Path) -> Optional[Path]:
    research_path = Path(research_dir)
    if not research_path.exists():
        return None

    query_tokens = _tokenize_query(query)
    if not query_tokens:
        return None

    for note_path in sorted(research_path.glob("*.md")):
        existing_query = str(read_frontmatter(note_path).get("query", ""))
        existing_tokens = _tokenize_query(existing_query)
        if not existing_tokens:
            continue
        overlap = len(query_tokens & existing_tokens) / len(query_tokens)
        if overlap >= 0.6:
            return note_path

    return None


def write_research_report(
    query: str,
    report: str,
    generated_at: Optional[datetime] = None,
) -> tuple[Path, bool]:
    generated_at = generated_at or datetime.now()
    ensure_vault_directories()
    paths = get_vault_paths()
    existing_note = find_existing_research_note(query, paths.research)
    if existing_note is not None:
        return existing_note, True

    note_path = paths.research / f"{generated_at.strftime('%Y-%m-%d')}-{slugify(query)}.md"
    note_path.write_text(report)
    return note_path, False


def render_research_report(
    query: str,
    papers: List[Dict[str, Any]],
    web_results: Optional[List[Dict[str, Any]]] = None,
    output: str = "vault",
    generated_at: Optional[datetime] = None,
    depth: str = "shallow",
) -> tuple[str, Optional[Path], bool]:
    report = format_research_report(
        query=query,
        papers=papers,
        web_results=web_results,
        generated_at=generated_at,
        depth=depth,
    )

    if output == "stdout":
        return report, None, False

    note_path, reused_existing = write_research_report(
        query=query,
        report=report,
        generated_at=generated_at,
    )
    return report, note_path, reused_existing


def ensure_knowledge_notes() -> list[Path]:
    ensure_vault_directories()
    paths = get_vault_paths()
    written_paths: list[Path] = []

    for filename, content in KNOWLEDGE_NOTES.items():
        note_path = paths.knowledge / filename
        if not note_path.exists():
            note_path.write_text(content)
        written_paths.append(note_path)

    return written_paths

if __name__ == "__main__":
    # Test
    test_q = "momentum strategy with volatility targeting"
    print(get_research_context(test_q))
