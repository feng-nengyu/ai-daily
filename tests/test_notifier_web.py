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


def test_render_site_first_run_puts_summaries_in_today_band(tmp_path: Path):
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
    # Both bands are present. Use unique section markers so we don't match
    # the header meta line, which mentions both 今日新增 / 归档 as counters.
    today_band = html.index('class="band today"')
    archive_band = html.index('class="band archive"')
    assert today_band < archive_band
    # Both items live in the today band (before the archive band marker)
    assert today_band < html.index("Foo Paper") < archive_band
    assert today_band < html.index("Bar Repo") < archive_band

    assert 'href="https://example.com/foo"' in html
    assert 'href="https://example.com/bar"' in html
    assert "核心创新 X" in html
    assert "Bar 创新" in html
    assert "LLM" in html and "agent" in html and "MCP" in html
    assert "arxiv:cs.AI" in html
    assert "github:agent" in html
    # Foo's links: real URL ≠ item url → render as 补充
    assert "补充：" in html
    assert 'href="https://example.com/code"' in html
    # Bar's links = "无" → suppressed
    assert "补充：无" not in html
    assert "代码/项目：" not in html

    # Below-threshold (no summary) not rendered
    assert "Below Threshold" not in html

    # Score-desc within today
    assert html.index("Foo Paper") < html.index("Bar Repo")

    assert result["today"] == 2
    assert result["archive"] == 0
    assert result["marked_surfaced"] == 2
    assert result["rendered"] == 2  # back-compat key
    assert result["output"] == str(index)


def test_render_site_second_run_same_day_moves_to_archive(tmp_path: Path):
    s = Storage(tmp_path / "t.db"); s.init()
    _seed(s)
    out_dir = tmp_path / "site"
    # First run: items become surfaced.
    r1 = render_site(s, min_score=7, within_days=30, top_n=100, output_dir=out_dir)
    assert r1["today"] == 2 and r1["archive"] == 0

    # Second run (no new items in between).
    r2 = render_site(s, min_score=7, within_days=30, top_n=100, output_dir=out_dir)
    s.close()
    assert r2["today"] == 0
    assert r2["archive"] == 2
    assert r2["marked_surfaced"] == 0  # nothing new to mark

    html = (out_dir / "index.html").read_text(encoding="utf-8")
    # Today band is empty
    assert "本批次无新条目" in html
    # Items now appear in archive band (after the archive band marker)
    archive_band = html.index('class="band archive"')
    assert html.index("Foo Paper") > archive_band
    assert html.index("Bar Repo") > archive_band


def test_render_site_empty_db_writes_empty_states(tmp_path: Path):
    s = Storage(tmp_path / "t.db"); s.init()
    out_dir = tmp_path / "site"
    result = render_site(s, min_score=7, within_days=30, top_n=100, output_dir=out_dir)
    s.close()
    assert result["today"] == 0
    assert result["archive"] == 0
    html = (out_dir / "index.html").read_text(encoding="utf-8")
    assert "本批次无新条目" in html
    assert "归档暂时为空" in html
