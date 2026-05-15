from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    pass


@dataclass
class Config:
    sources: list[dict[str, Any]]
    keywords: list[str]
    fetch_window_hours: int = 36
    raw_preferences: dict[str, Any] = field(default_factory=dict)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"config file not found: {path}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"{path} must be a YAML mapping at top level")
    return data


def _validate_source(src: dict[str, Any]) -> None:
    for required in ("name", "type"):
        if required not in src:
            raise ConfigError(
                f"source {src!r} missing required field {required!r}"
            )


def load_config(
    sources_path: Path = Path("config/sources.yaml"),
    preferences_path: Path = Path("config/preferences.yaml"),
) -> Config:
    sources_doc = _load_yaml(sources_path)
    prefs_doc = _load_yaml(preferences_path)

    sources = sources_doc.get("sources", [])
    if not isinstance(sources, list):
        raise ConfigError("`sources` must be a list")
    for src in sources:
        _validate_source(src)

    keywords = prefs_doc.get("keywords", [])
    if not isinstance(keywords, list):
        raise ConfigError("`keywords` must be a list")

    fetch_window = prefs_doc.get("fetch_window_hours", 36)
    if isinstance(fetch_window, bool) or not isinstance(fetch_window, int) or fetch_window <= 0:
        raise ConfigError("`fetch_window_hours` must be a positive integer")

    return Config(
        sources=sources,
        keywords=keywords,
        fetch_window_hours=fetch_window,
        raw_preferences=prefs_doc,
    )
