"""Structured logging setup — one place to configure format/level for both services.
JSON-ish structured lines in production, readable plain text in dev.
"""
import logging
import sys

from .config import get_settings


def setup_logging():
    settings = get_settings()
    level = logging.INFO if settings.is_production else logging.DEBUG

    fmt = (
        "%(asctime)s %(levelname)s %(name)s %(message)s"
        if settings.is_production
        else "%(levelname)s %(name)s: %(message)s"
    )

    logging.basicConfig(level=level, format=fmt, stream=sys.stdout, force=True)

    # quiet noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
