import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import settings

DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging() -> None:
    """Configure logging from environment variables.

    LOG_LEVEL  - DEBUG / INFO / WARNING / ERROR / CRITICAL (default INFO)
    LOG_FORMAT - format string for logging.Formatter
    LOG_FILE   - optional path to a rotating log file
    """
    level_name = (settings.log_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    format_string = settings.log_format or DEFAULT_LOG_FORMAT

    try:
        formatter = logging.Formatter(format_string)
    except ValueError:
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    if settings.log_file:
        log_path = Path(settings.log_file)
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=5_000_000,
                backupCount=3,
                encoding="utf-8",
            )
        except OSError:
            logging.getLogger(__name__).warning(
                "Cannot open log file %s; logging to console only", log_path
            )
        else:
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)

    # Uvicorn duplicates every request in its access log; our middleware
    # already logs requests with the configured level and format.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
