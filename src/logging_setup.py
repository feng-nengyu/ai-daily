import logging
import sys

_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    root = logging.getLogger()
    root.setLevel(level)
    if not any(getattr(h, "_ai_daily_marker", False) for h in root.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_FORMAT, _DATE_FORMAT))
        handler._ai_daily_marker = True  # type: ignore[attr-defined]
        root.addHandler(handler)
    return root
