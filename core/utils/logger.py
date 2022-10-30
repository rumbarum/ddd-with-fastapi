import logging

from core.config import config


def init_logger():
    DEFAULT_LOGGING = {
        # 버전 정보 필수
        "version": 1,
        # 다른 logger Disable, Default True
        "disable_existing_loggers": False,
        # filter setting
        "filters": {},
        # formatter setting
        "formatters": {
            "basic": {
                "format": "%(asctime)s %(levelname)s: %(message)s",
            },
        },
        # handler setting
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "basic",
            },
        },
        # 별도 logger 필요시 추가
        "loggers": {},
        # root logger setting
        "root": {
            "handlers": ["console"],
            # 조건에 따라 logger 레벨 세팅, 또는 고정 할 것
            "level": "DEBUG" if config.DEBUG else "INFO",
        },
    }
    # config 주입
    logging.config.dictConfig(DEFAULT_LOGGING)
