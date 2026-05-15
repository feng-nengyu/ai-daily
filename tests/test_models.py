from datetime import datetime, timezone

from src.models import Item


def test_item_construction_minimal():
    item = Item(
        url="https://arxiv.org/abs/2401.00001",
        title="Sample Paper",
        content="Abstract content",
        published_at=datetime(2026, 5, 14, 12, 0, tzinfo=timezone.utc),
        source="arxiv:cs.AI",
    )
    assert item.url == "https://arxiv.org/abs/2401.00001"
    assert item.title == "Sample Paper"
    assert item.source == "arxiv:cs.AI"
    assert item.raw == {}  # default


def test_item_with_raw_payload():
    raw = {"id": "2401.00001", "categories": ["cs.AI"]}
    item = Item(
        url="https://arxiv.org/abs/2401.00001",
        title="Sample Paper",
        content="Abstract",
        published_at=datetime(2026, 5, 14, tzinfo=timezone.utc),
        source="arxiv:cs.AI",
        raw=raw,
    )
    assert item.raw == raw


def test_item_equality_by_value():
    a = Item(
        url="https://example.com/x",
        title="x",
        content="",
        published_at=datetime(2026, 5, 14, tzinfo=timezone.utc),
        source="rss:example",
    )
    b = Item(
        url="https://example.com/x",
        title="x",
        content="",
        published_at=datetime(2026, 5, 14, tzinfo=timezone.utc),
        source="rss:example",
    )
    assert a == b
