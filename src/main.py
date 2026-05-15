import argparse
import asyncio
import logging
import sys
from pathlib import Path

from src.config import load_config
from src.dedup import dedup_by_url
from src.fetchers import fetch_all
from src.logging_setup import setup_logging
from src.storage import Storage


logger = logging.getLogger(__name__)


async def run_fetch(
    sources_path: Path = Path("config/sources.yaml"),
    preferences_path: Path = Path("config/preferences.yaml"),
    db_path: Path = Path("data/ai_daily.db"),
) -> dict[str, int]:
    config = load_config(sources_path=sources_path, preferences_path=preferences_path)
    storage = Storage(db_path)
    storage.init()
    try:
        items = await fetch_all(config.sources, window_hours=config.fetch_window_hours)
        fetched = len(items)
        unique = dedup_by_url(items, storage)
        deduped = len(unique)
        storage.record_items(unique)
        stored = deduped  # records dedup further by PK but our dedup_by_url already aligned
        logger.info(
            "fetch summary: fetched=%d deduped=%d stored=%d",
            fetched, deduped, stored,
        )
        return {"fetched": fetched, "deduped": deduped, "stored": stored}
    finally:
        storage.close()


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="ai-daily")
    sub = parser.add_subparsers(dest="command", required=True)

    fetch_p = sub.add_parser("fetch", help="Fetch all sources and store new URLs")
    fetch_p.add_argument("--sources", default="config/sources.yaml")
    fetch_p.add_argument("--preferences", default="config/preferences.yaml")
    fetch_p.add_argument("--db", default="data/ai_daily.db")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    if args.command == "fetch":
        asyncio.run(
            run_fetch(
                sources_path=Path(args.sources),
                preferences_path=Path(args.preferences),
                db_path=Path(args.db),
            )
        )
        return 0
    raise SystemExit(f"unknown command: {args.command}")


if __name__ == "__main__":
    sys.exit(main())
