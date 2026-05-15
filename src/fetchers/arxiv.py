import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import feedparser
import httpx
from dateutil import parser as date_parser

from src.models import Item


logger = logging.getLogger(__name__)

_API_URL = "https://export.arxiv.org/api/query"


def _build_query(categories: list[str]) -> str:
    parts = [f"cat:{c}" for c in categories]
    return " OR ".join(parts)


async def fetch_arxiv(source: dict[str, Any], window_hours: int) -> list[Item]:
    name = source["name"]
    categories = source.get("categories", ["cs.AI"])
    max_results = int(source.get("max_results", 50))
    params = {
        "search_query": _build_query(categories),
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{_API_URL}?{urlencode(params)}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        body = response.text

    feed = feedparser.parse(body)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    items: list[Item] = []
    for entry in feed.entries:
        published_raw = entry.get("published") or entry.get("updated")
        if not published_raw:
            continue
        try:
            published_at = date_parser.parse(published_raw)
        except (ValueError, TypeError):
            continue
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        if published_at < cutoff:
            continue
        link = entry.get("link") or entry.get("id")
        title = (entry.get("title") or "").strip()
        if not link or not title:
            continue
        items.append(
            Item(
                url=link,
                title=title,
                content=(entry.get("summary") or "").strip(),
                published_at=published_at,
                source=f"arxiv:{name}",
                raw=dict(entry),
            )
        )
    return items
