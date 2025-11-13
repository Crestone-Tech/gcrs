import logging
import logging.config

from typing import Optional


LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d] - %(message)s"

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = "logs/app.log"):
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": LOG_FORMAT
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "standard",
                "filename": log_file,
                "maxBytes": 1024 * 1024 * 5, # 5MB  
                "backupCount": 5, # keep 5 backup files
                "encoding": "utf-8"
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": log_level,
        },
    }
    logging.config.dictConfig(logging_config)
    return logging.getLogger("app")

