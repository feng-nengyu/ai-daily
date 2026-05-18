from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.storage import Storage


def render_site(
    storage: Storage,
    *,
    min_score: int,
    within_days: int,
    top_n: int,
    output_dir: Path = Path("site"),
    templates_dir: Path = Path("templates"),
) -> dict:
    """Render the daily digest page (今日新增 + 归档) to a single HTML file.

    Today's batch = summaries with surfaced_at IS NULL and score >= min_score.
    Archive = surfaced summaries within the last `within_days`.

    After the file is written, today's batch is marked surfaced so a re-run
    in the same session yields an empty today section (strict batch semantics
    — keeps the future email/wechat push aligned with the web view).

    `top_n` is currently unused at the storage layer; kept in the signature
    for forward-compat with a planned per-band cap.
    """
    today = storage.get_today_summaries(min_score=min_score)
    archive = storage.get_archive_summaries(
        min_score=min_score, within_days=within_days,
    )

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("index.html.j2")
    html = template.render(
        today=today,
        archive=archive,
        within_days=within_days,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "index.html"
    output_path.write_text(html, encoding="utf-8")

    marked = storage.mark_surfaced([a.url for a in today])

    return {
        "today": len(today),
        "archive": len(archive),
        "marked_surfaced": marked,
        "output": str(output_path),
        # Back-compat key used by tests written against the Stage 3-lite shape.
        "rendered": len(today) + len(archive),
    }
