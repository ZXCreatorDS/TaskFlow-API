"""Demonstrate all standard Python logging levels.

Run locally:
    python -m app.logging_demo

Run inside the API container:
    docker compose exec api python -m app.logging_demo

The default level for this demo is DEBUG, but it can be overridden:
    LOG_LEVEL=WARNING python -m app.logging_demo
"""

import logging
import os

os.environ.setdefault("LOG_LEVEL", "DEBUG")

from app.logging_config import configure_logging  # noqa: E402

logger = logging.getLogger("taskflow.logging_demo")


def emit_all_levels(target: logging.Logger | None = None) -> None:
    """Emit one message at each standard logging level."""
    log = target or logger
    log.debug("DEBUG: detailed diagnostic information")
    log.info("INFO: normal application event")
    log.warning("WARNING: unexpected but recoverable situation")
    log.error("ERROR: operation failed")
    log.critical("CRITICAL: application cannot continue")


def main() -> None:
    configure_logging()
    emit_all_levels()


if __name__ == "__main__":
    main()
