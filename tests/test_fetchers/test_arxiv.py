import re

import pytest
from freezegun import freeze_time

from src.fetchers.arxiv import fetch_arxiv


@pytest.mark.asyncio
@freeze_time("2026-05-15 12:00:00")
async def test_fetch_arxiv_returns_recent_papers(httpx_mock, arxiv_response_xml):
    httpx_mock.add_response(
        url=re.compile(r"https://export\.arxiv\.org/api/query.*"),
        text=arxiv_response_xml,
    )
    source = {
        "name": "arxiv-cs-ai",
        "type": "arxiv",
        "categories": ["cs.AI"],
        "max_results": 50,
    }
    items = await fetch_arxiv(source, window_hours=36)
    urls = [i.url for i in items]
    assert "http://arxiv.org/abs/2405.00001v1" in urls
    assert "http://arxiv.org/abs/2401.99999v1" not in urls
    new_item = next(i for i in items if i.url == "http://arxiv.org/abs/2405.00001v1")
    assert new_item.title == "A New Agent Framework"
    assert new_item.source == "arxiv:arxiv-cs-ai"
    assert "novel agent framework" in new_item.content
