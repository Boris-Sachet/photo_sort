import os
from logging.config import dictConfig

logger_config = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {"default": {"format": "%(asctime)s - %(levelname)s - %(module)s - %(message)s"}},
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        # "file": {
        #     "class": "logging.RotatingFileHandler",
        #     "formater": "default",
        #     "filename": "photo_sort.log",
        #     "maxBtytes": 5 * 1024 * 1024,
        # }
    },
    "loggers": {"": {"handlers": ["default"], "level": os.getenv("LOGLEVEL", "INFO").upper()}},
}

dictConfig(logger_config)
