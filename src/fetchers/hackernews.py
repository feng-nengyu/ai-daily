import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from src.models import Item


logger = logging.getLogger(__name__)

_API_URL = "https://hn.algolia.com/api/v1/search"


async def fetch_hackernews(source: dict[str, Any], window_hours: int) -> list[Item]:
    name = source["name"]
    query = source["query"]
    min_points = int(source.get("min_points", 100))

    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    cutoff_ts = int(cutoff.timestamp())

    params = {
        "query": query,
        "tags": "story",
        "numericFilters": f"points>={min_points},created_at_i>={cutoff_ts}",
        "hitsPerPage": 50,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(_API_URL, params=params)
        response.raise_for_status()
        payload = response.json()

    items: list[Item] = []
    for hit in payload.get("hits", []):
        url = hit.get("url")
        if not url:
            continue
        points = int(hit.get("points", 0))
        if points < min_points:
            continue
        created_ts = hit.get("created_at_i")
        if not created_ts:
            continue
        published_at = datetime.fromtimestamp(int(created_ts), tz=timezone.utc)
        if published_at < cutoff:
            continue
        title = hit.get("title") or ""
        if not title:
            continue
        items.append(
            Item(
                url=url,
                title=title,
                content=hit.get("story_text") or "",
                published_at=published_at,
                source=f"hackernews:{name}",
                raw=hit,
            )
        )
    return items
