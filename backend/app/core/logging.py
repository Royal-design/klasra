import json
import logging
from datetime import datetime, timezone


class JsonLogFormatter(logging.Formatter):
    """Structured JSON formatter keeping logs PII-safe and machine-parseable."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in ("request_id", "method", "path", "status_code", "duration_ms"):
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(*, app_env: str) -> None:
    root = logging.getLogger()
    if app_env == "production":
        handler = logging.StreamHandler()
        handler.setFormatter(JsonLogFormatter())
        root.handlers = [handler]
        root.setLevel(logging.INFO)
