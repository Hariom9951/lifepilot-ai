import logging.config
import os

from app.core.config.settings import settings


def setup_logging() -> None:
    """
    Setup structured rotating file and console logging configurations.
    Create logs directory on startup if it doesn't exist.
    """
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)

    log_level = settings.LOG_LEVEL.upper()

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d) - %(message)s"
            },
            "simple": {"format": "%(asctime)s [%(levelname)s] - %(message)s"},
            "access": {"format": "%(asctime)s - %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": log_level,
            },
            "app_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": os.path.join(logs_dir, "app.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "standard",
                "level": log_level,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": os.path.join(logs_dir, "error.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "standard",
                "level": "WARNING",
                "encoding": "utf-8",
            },
            "access_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": os.path.join(logs_dir, "access.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "access",
                "level": "INFO",
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "app_file", "error_file"],
                "level": log_level,
                "propagate": True,
            },
            "app.middleware.timing": {
                "handlers": ["access_file"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)
