import logging
import sys
import json
from datetime import datetime, timezone
from apps.api.app.core.config import settings

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "workspace_id"):
            log_data["workspace_id"] = record.workspace_id
        return json.dumps(log_data)

def setup_logging():
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    if settings.ENVIRONMENT == "production":
        handler.setFormatter(JSONFormatter())
    else:
        standard_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        handler.setFormatter(logging.Formatter(standard_format))

    logger.handlers = [handler]
    return logger

logger = logging.getLogger("modelops")
