import logging
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "handlers": {
        "httpx_handler": {
            "class": "logging.StreamHandler",
            "formatter": "http",
            "stream": "ext://sys.stdout",
        },
        "default": {
            "class": "logging.FileHandler",
            "formatter": "basic_formatter",
            "filename": "logs.log",
        },
    },
    "formatters": {
        "http": {
            "format": "%(levelname)s [%(asctime)s] %(name)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "basic_formatter": {
            "format": "[%(asctime)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "loggers": {
        "httpx": {
            "handlers": ["httpx_handler"],
            "level": "INFO",
        },
        "httpcore": {
            "handlers": ["httpx_handler"],
            "level": "WARNING",
        },
        "client": {"handlers": ["default"], "level": "INFO"},
    },
}

logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger("client")