from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def rss_feed_xml(fixtures_dir: Path) -> str:
    return (fixtures_dir / "rss_feed.xml").read_text(encoding="utf-8")
