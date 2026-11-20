import json
import logging

from app.logging_config import JsonFormatter, configure_logging


def test_json_formatter_emits_one_object():
    record = logging.LogRecord("ragforge", logging.INFO, __file__, 1, "hello %s", ("x",), None)
    data = json.loads(JsonFormatter().format(record))
    assert data["msg"] == "hello x" and data["level"] == "INFO"


def test_configure_logging_is_idempotent():
    configure_logging("DEBUG")
    configure_logging("INFO", json_logs=True)
    logger = logging.getLogger("ragforge")
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0].formatter, JsonFormatter)
    assert logger.level == logging.INFO
