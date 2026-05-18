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
    """Render top summarized items to a single self-contained HTML file.

    Only items that have BOTH a score >= min_score AND a summary attached
    are rendered. Sort: score desc, then published_at desc.
    """
    analyses = [
        a for a in storage.get_top_summaries(
            min_score=min_score, limit=top_n, within_days=within_days,
        )
        if a.summary is not None
    ]

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("index.html.j2")
    html = template.render(
        analyses=analyses,
        within_days=within_days,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "index.html"
    output_path.write_text(html, encoding="utf-8")

    return {"rendered": len(analyses), "output": str(output_path)}
