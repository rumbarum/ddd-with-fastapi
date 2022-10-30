import os

import yaml
from pydantic import BaseModel, BaseSettings

ROOT_DIR = os.path.dirname(os.path.dirname((os.path.abspath(__file__))))

with open(f"{ROOT_DIR}/config.yaml", "r") as f:
    config_dict: dict = yaml.safe_load(f)


class ExtServer(BaseModel):
    ADDRESS: str
    AUTHORIZATION: str


class Config(BaseSettings):
    ENV: str = "development"
    DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 5000
    WRITER_DB_URL: str
    READER_DB_URL: str
    JWT_SECRET_KEY: str = "fastapi"
    JWT_ALGORITHM: str = "HS256"
    SENTRY_SDN: str = None
    CELERY_BROKER_URL: str = None
    CELERY_BACKEND_URL: str = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    ML_SERVER: ExtServer
    AUTH_SERVER: ExtServer


def get_config():
    env = os.getenv("ENV", "local")
    return Config(**(config_dict.get(env.upper())))


config: Config = get_config()
