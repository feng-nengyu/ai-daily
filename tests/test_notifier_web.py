from datetime import datetime, timezone
from pathlib import Path

from src.models import Item, Score, Summary
from src.notifier.web import render_site
from src.storage import Storage


def _seed(s: Storage):
    now = datetime.now(timezone.utc)
    s.record_items([
        Item(url="https://example.com/foo", title="Foo Paper", content="...",
             published_at=now, source="arxiv:cs.AI"),
        Item(url="https://example.com/bar", title="Bar Repo", content="...",
             published_at=now, source="github:agent"),
        Item(url="https://example.com/below", title="Below Threshold", content="...",
             published_at=now, source="rss:misc"),
    ])
    s.save_score("https://example.com/foo",
                 Score(score=9, tags=["LLM", "agent"], model="m", cost_usd=0.001))
    s.save_summary("https://example.com/foo",
                   Summary(innovation="核心创新 X",
                           approach="技术方案 Y",
                           metrics="50% 提升",
                           links="https://example.com/code",
                           why_relevant="与关键词强相关",
                           model="m", cost_usd=0.01))
    s.save_score("https://example.com/bar",
                 Score(score=7, tags=["MCP"], model="m", cost_usd=0.001))
    s.save_summary("https://example.com/bar",
                   Summary(innovation="Bar 创新", approach="A2",
                           metrics="未披露", links="无",
                           why_relevant="关注 MCP 用户值得看",
                           model="m", cost_usd=0.01))
    # below: scored but no summary
    s.save_score("https://example.com/below",
                 Score(score=4, tags=[], model="m", cost_usd=0.001))


def test_render_site_produces_self_contained_html(tmp_path: Path):
    s = Storage(tmp_path / "t.db"); s.init()
    _seed(s)
    out_dir = tmp_path / "site"
    result = render_site(s, min_score=7, within_days=30, top_n=100, output_dir=out_dir)
    s.close()

    index = out_dir / "index.html"
    assert index.exists()
    html = index.read_text(encoding="utf-8")

    # Self-contained — inline style, no external scripts
    assert "<style>" in html
    assert "<script" not in html

    # Both summarized items appear
    assert "Foo Paper" in html
    assert "Bar Repo" in html
    # Their URLs are present as href
    assert 'href="https://example.com/foo"' in html
    assert 'href="https://example.com/bar"' in html
    # Their summary content rendered
    assert "核心创新 X" in html
    assert "Bar 创新" in html
    # tags rendered
    assert "LLM" in html and "agent" in html and "MCP" in html
    # source badges
    assert "arxiv:cs.AI" in html
    assert "github:agent" in html
    # Foo's links is a real URL distinct from its item url → render as "补充" link
    assert "补充：" in html
    assert 'href="https://example.com/code"' in html
    # Bar's links is "无" → not a URL → no "补充" line for bar
    # (we check via absence of a card-foot link to a non-existent path)
    assert "补充：无" not in html
    # The old wording was changed
    assert "代码/项目：" not in html

    # Below-threshold item not rendered
    assert "Below Threshold" not in html

    # Higher-score item appears BEFORE lower-score one in the HTML
    assert html.index("Foo Paper") < html.index("Bar Repo")

    # Returned summary
    assert result["rendered"] == 2
    assert result["output"] == str(index)


def test_render_site_empty_db_writes_empty_state(tmp_path: Path):
    s = Storage(tmp_path / "t.db"); s.init()
    out_dir = tmp_path / "site"
    result = render_site(s, min_score=7, within_days=30, top_n=100, output_dir=out_dir)
    s.close()
    assert result["rendered"] == 0
    html = (out_dir / "index.html").read_text(encoding="utf-8")
    assert "还没有可展示" in html
