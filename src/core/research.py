import arxiv
import bm25s
import json
import os
import re
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

CACHE_FILE = "experiments/results/research_cache.json"
WEB_CACHE_FILE = "experiments/results/web_research_cache.json"

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

if __name__ == "__main__":
    # Test
    test_q = "momentum strategy with volatility targeting"
    print(get_research_context(test_q))
