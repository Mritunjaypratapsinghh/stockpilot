"""Structured JSON logging — production-grade observability."""

import json
import logging
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Output logs as JSON for structured log aggregation (ELK, CloudWatch, Datadog)."""

    def format(self, record: logging.LogRecord) -> str:
        from ..middleware.correlation import get_request_id

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "request_id": get_request_id(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        # Include extra fields passed via logger.info("msg", extra={...})
        for key in ("user_id", "endpoint", "method", "status_code", "duration_ms", "request_id"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)
        return json.dumps(log_entry, default=str)


def setup_logger(name: str = "stockpilot") -> logging.Logger:
    log = logging.getLogger(name)
    if not log.handlers:
        log.setLevel(logging.INFO)

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        log.addHandler(handler)

    return log


logger = setup_logger()
