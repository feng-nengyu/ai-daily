import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from src.models import Item


_SCHEMA = """
CREATE TABLE IF NOT EXISTS seen_urls (
    url TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    published_at TEXT NOT NULL,
    first_seen TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_seen_urls_first_seen
    ON seen_urls(first_seen);
"""


class Storage:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None

    def init(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _require_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Storage.init() not called")
        return self._conn

    def seen_urls(self, urls: Iterable[str]) -> set[str]:
        url_list = list(urls)
        if not url_list:
            return set()
        conn = self._require_conn()
        placeholders = ",".join("?" * len(url_list))
        rows = conn.execute(
            f"SELECT url FROM seen_urls WHERE url IN ({placeholders})",
            url_list,
        ).fetchall()
        return {row["url"] for row in rows}

    def record_items(self, items: Iterable[Item]) -> None:
        conn = self._require_conn()
        now = datetime.now(timezone.utc).isoformat()
        rows = [
            (
                item.url,
                item.title,
                item.source,
                item.published_at.isoformat(),
                now,
            )
            for item in items
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO seen_urls"
            " (url, title, source, published_at, first_seen)"
            " VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()

    def fetch_item_row(self, url: str) -> dict:
        conn = self._require_conn()
        row = conn.execute(
            "SELECT * FROM seen_urls WHERE url = ?", (url,)
        ).fetchone()
        return dict(row) if row else {}
