"""Tavily search grounding layer."""
import httpx
from app.config import get_settings
from app.schemas import Grounding, SearchHit


class SearchError(RuntimeError):
    pass


async def ground(query: str) -> Grounding:
    s = get_settings()
    if not s.tavily_api_key:
        raise SearchError("TAVILY_API_KEY is not set (or enable MOCK_MODE=true).")
    if not query.strip():
        return Grounding(query=query)
    payload = {
        "query": query,
        "search_depth": "advanced",
        "max_results": s.tavily_max_results,
        "include_answer": True,
    }
    headers = {"Authorization": f"Bearer {s.tavily_api_key}"}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post("https://api.tavily.com/search", json=payload, headers=headers)
    if r.status_code >= 400:
        raise SearchError(f"Tavily error {r.status_code}: {r.text[:300]}")
    d = r.json()
    hits = [
        SearchHit(
            title=x.get("title", ""),
            url=x.get("url", ""),
            snippet=(x.get("content") or "")[:600],
            score=x.get("score"),
        )
        for x in d.get("results", [])
    ]
    return Grounding(query=query, answer=d.get("answer"), results=hits)
