import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from src.models import Item, Score, Summary
from src.storage import Storage


def _item(url: str, content: str = "body", title: str = "t", days_ago: int = 0) -> Item:
    return Item(
        url=url,
        title=title,
        content=content,
        published_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
        source="test",
        raw={"k": "v"},
    )


def test_items_table_persists_full_content(tmp_path: Path):
    s = Storage(tmp_path / "t.db")
    s.init()
    s.record_items([_item("https://a", content="long body about LLMs")])
    rows = s.get_items_by_urls(["https://a"])
    assert len(rows) == 1
    assert rows[0].content == "long body about LLMs"
    assert rows[0].raw == {"k": "v"}
    s.close()


def test_seen_urls_still_filters_known(tmp_path: Path):
    s = Storage(tmp_path / "t.db")
    s.init()
    s.record_items([_item("https://a")])
    assert s.seen_urls(["https://a", "https://b"]) == {"https://a"}
    s.close()


def test_save_score_and_summary_roundtrip(tmp_path: Path):
    s = Storage(tmp_path / "t.db")
    s.init()
    s.record_items([_item("https://a")])
    s.save_score("https://a", Score(score=8, tags=["LLM", "agent"], model="m1", cost_usd=0.001))
    s.save_summary(
        "https://a",
        Summary(
            innovation="x",
            approach="y",
            metrics="z",
            links="https://a",
            why_relevant="r",
            model="m2",
            cost_usd=0.01,
        ),
    )
    analyses = s.get_top_summaries(min_score=7, limit=10, within_days=1)
    assert len(analyses) == 1
    a = analyses[0]
    assert a.url == "https://a"
    assert a.score.score == 8
    assert a.score.tags == ["LLM", "agent"]
    assert a.summary is not None
    assert a.summary.innovation == "x"
    assert a.total_cost_usd == pytest.approx(0.011)
    s.close()


def test_get_unscored_items_returns_only_recent_without_score(tmp_path: Path):
    s = Storage(tmp_path / "t.db")
    s.init()
    s.record_items([
        _item("https://a", days_ago=0),
        _item("https://b", days_ago=0),
        _item("https://old", days_ago=30),
    ])
    s.save_score("https://a", Score(score=3, tags=[], model="m", cost_usd=0.0))
    unscored = s.get_unscored_items(within_days=7)
    urls = {it.url for it in unscored}
    assert urls == {"https://b"}  # old too old, a already scored
    s.close()


def test_init_drops_old_seen_urls_table(tmp_path: Path):
    db = tmp_path / "t.db"
    import sqlite3
    conn = sqlite3.connect(db)
    conn.executescript(
        "CREATE TABLE seen_urls (url TEXT PRIMARY KEY, title TEXT, source TEXT,"
        " published_at TEXT, first_seen TEXT);"
        " INSERT INTO seen_urls VALUES ('https://legacy','t','s','2026-01-01','2026-01-01');"
    )
    conn.commit()
    conn.close()

    s = Storage(db)
    s.init()
    assert s.seen_urls(["https://legacy"]) == set()
    s.close()
