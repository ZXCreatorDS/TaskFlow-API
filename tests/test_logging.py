import logging

from app.logging_demo import emit_all_levels


def test_all_logging_levels(caplog):
    logger = logging.getLogger("tests.logging_demo")

    with caplog.at_level(logging.DEBUG, logger=logger.name):
        emit_all_levels(logger)

    levels = {record.levelname for record in caplog.records}
    assert levels >= {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
