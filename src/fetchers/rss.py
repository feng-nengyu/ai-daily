import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import feedparser
import httpx
from dateutil import parser as date_parser

from src.fetchers._http import USER_AGENT
from src.models import Item


logger = logging.getLogger(__name__)


def _parse_date(entry: dict) -> datetime | None:
    raw = entry.get("published") or entry.get("updated") or entry.get("pubDate")
    if not raw:
        if "published_parsed" in entry and entry.get("published_parsed"):
            return datetime(*entry["published_parsed"][:6], tzinfo=timezone.utc)
        return None
    try:
        dt = date_parser.parse(raw)
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


async def fetch_rss(source: dict[str, Any], window_hours: int) -> list[Item]:
    url = source["url"]
    name = source["name"]
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
        response = await client.get(url)
        response.raise_for_status()
        body = response.text

    feed = feedparser.parse(body)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    items: list[Item] = []
    for entry in feed.entries:
        published_at = _parse_date(entry)
        if published_at is None:
            logger.debug("rss:%s skip entry without date: %s", name, entry.get("link"))
            continue
        if published_at < cutoff:
            continue
        link = entry.get("link")
        title = entry.get("title")
        if not link or not title:
            continue
        items.append(
            Item(
                url=link,
                title=title,
                content=entry.get("summary", "") or entry.get("description", ""),
                published_at=published_at,
                source=f"rss:{name}",
                raw=dict(entry),
            )
        )
    return items
