import json
import logging
import sys
from datetime import datetime, timezone
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class ColorFormatter(logging.Formatter):
    """Colored formatter for local development"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[41m",  # Red background
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        message = super().format(record)
        return f"{color}{message}{self.RESET}"


class JsonFormatter(logging.Formatter):
    """Minimal JSON formatter for production logs."""

    def format(self, record):
        payload = {
            "time": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "func": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "location": f"{record.pathname}:{record.lineno}",
        }

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "asctime",
            }:
                continue
            if key.startswith("_"):
                continue
            payload[key] = self._json_safe(value)

        return json.dumps(payload, ensure_ascii=True)

    @staticmethod
    def _json_safe(value):
        try:
            json.dumps(value)
            return value
        except Exception:
            return repr(value)


class Settings(BaseSettings):
    APP_NAME: str = "mro_botasaurus"
    LOCAL_DEV: bool = (
        False  # True for local development (colored logs), False for production (plain logs)
    )
    LOG_LEVEL: str = "INFO"  # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    INACTIVITY_TIMEOUT: int = (
        9000  # Global timeout for operations without specific timeout
    )
    MAX_WORKERS: int = 12  # Number of concurrent browser operations
    DEFAULT_OPERATION_TIMEOUT: int = (
        30  # Default timeout for individual operations (seconds)
    )
    BROWSER_POOL_SIZE: int = 12  # Number of browsers to keep in the pool
    MIN_OPERATION_DELAY: float = (
        0.00  # Delay between operations to reduce CPU spikes (seconds)
    )

    # Browser Health Check Settings
    HEALTH_CHECK_ENABLED: bool = True  # Enable health checks on browser acquisition
    HEALTH_CHECK_TIMEOUT: float = 1.0  # Max time for health check (seconds)
    HEALTH_CHECK_MAX_RETRIES: int = 3  # Max attempts to find healthy browser
    AUTO_RECREATE_UNHEALTHY: bool = True  # Automatically recreate unhealthy browsers

    PROXY_USER: str = "msuppl"
    PROXY_PASS: str = "S0GYgQ8o"
    PROXY_PORT: str = "29842"

    PROXY_IPS: List[str] = [
        "31.131.10.206",
        "23.106.20.16",
        "207.230.104.18",
        "151.248.88.119",
        "207.230.107.224",
        "31.131.10.106",
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


def setup_logger():
    """Setup stdout logging - Docker awslogs driver handles log shipping in production"""
    logger = logging.getLogger(settings.APP_NAME)

    # Set log level from configuration
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    logger.handlers.clear()

    # Use colors in LOCAL_DEV mode; JSON logs in production for easy parsing
    if settings.LOCAL_DEV:
        formatter = ColorFormatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
        )
    else:
        formatter = JsonFormatter()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


settings = Settings()
logger = setup_logger()
