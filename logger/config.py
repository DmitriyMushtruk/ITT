import logging
import logging.config
import sys
from pathlib import Path

LOG_FILE_PATH = Path(__file__).parent / "app.log"

def setup_logging() -> None:
    """Set up logging configuration.

    Configure logging settings for the application, enabling both console and file outputs
    with a standardized format. This function sets up loggers with various levels and handlers
    to customize behavior for specific components of the application (e.g., `sqlalchemy.engine`).
    The logging configuration is applied using Python's `logging.config.dictConfig`.
    """
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,

        "formatters": {
            "standard": {
                "format": "[%(asctime)s] %(levelname)s:     %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.FileHandler",
                "level": "INFO",
                "formatter": "standard",
                "filename": LOG_FILE_PATH,
                "encoding": "utf-8",
            },
        },

        "loggers": {
            "sqlalchemy.engine": {
                "handlers": ["console", "file"],
                "level": "WARNING",
                "propagate": False,
            },
            "base": {
                "handlers": ["console", "file"],
                "level": "WARNING",
                "propagate": False,
            },
        },

        "root": {
            "level": "INFO",
            "handlers": ["console", "file"],
        },
    }

    logging.config.dictConfig(logging_config)
