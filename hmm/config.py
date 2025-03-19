import base64

import random
import sys
from functools import cache
from pathlib import Path
from typing import Literal

from dotenv import find_dotenv, load_dotenv
from loguru import logger
from pydantic import Field, PostgresDsn, computed_field, model_validator
from pydantic_settings import BaseSettings

LOGGING_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


class EnvSettings(BaseSettings):
    name: str = ".env"
    ignore: bool = False

    @property
    def is_env_path_abs(self):
        return Path(self.name).is_absolute()


class LicenceSettings(BaseSettings):
    @computed_field
    @property
    def base_url(self) -> str:
        return "http://lcs-server:8000"


class App(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    name: str = "V"
    PAGINATOR_MAX_LIMIT: int = Field(200, ge=1)
    container_label: str = "com.vps.select"
    nginx_on: bool = False
    FIFO_DIR: str = Field("out")

    @computed_field
    @property
    def fifo_inp(self) -> Path:
        return Path(f"{self.FIFO_DIR}/1t2.fifo").resolve()

    @computed_field
    @property
    def fifo_out(self) -> Path:
        return Path(f"{self.FIFO_DIR}/2t1.fifo").resolve()

    class Config:
        env_prefix = "server_"


class Docker(BaseSettings):
    host: str = "unix:///var/run/docker.sock"
    containers: str

    class Config:
        env_prefix = "docker_"

    @property
    def docker_environment(self):
        return {
            f"{self.Config.env_prefix}{k}".upper(): v
            for k, v in self.model_dump().items()
        }

    @computed_field
    @property
    def containers_list(self) -> list[str]:
        return self.containers.split(";")


class Logging(BaseSettings):
    # logging
    to_file: bool = True
    log_dir: str | None = "./logs"
    level: Literal[LOGGING_LEVELS] = "DEBUG"  # type: ignore
    db_log: bool = False

    @property
    def log_file_format(self) -> str:
        return "log_{time}.json"

    @property
    def log_path(self) -> str | None:
        if not self.to_file:
            return None
        fp = Path(self.log_dir)
        fp.parent.mkdir(parents=True, exist_ok=True)
        return str(fp / self.log_file_format)

    @computed_field
    @property
    def is_debug(self) -> bool:
        return self.level == "DEBUG"

    class Config:
        env_prefix = "log_"


class PostgresSettings(BaseSettings):
    user: str = "postgres"
    password: str = "postgres"
    db: str = "hmm"

    class Config:
        env_prefix = "postgres_"


class DbSettings(BaseSettings):
    pg_creds: PostgresSettings = Field(default_factory=PostgresSettings)
    host: str = "localhost"
    port: str = "5432"
    pool_size: int = 1

    driver_schema: str = "postgresql+asyncpg"

    class Config:
        env_prefix = "database_"

    @property
    def db_url(self) -> PostgresDsn:
        return (
            f"{self.driver_schema}://"
            f"{self.pg_creds.user}:{self.pg_creds.password}@"
            f"{self.host}:{self.port}"
            f"/{self.pg_creds.db}"
        )


class Api(BaseSettings):
    versions: list[int] = [1]
    base_version: int = 1

    api_prefix: str = "/api"
    docs_disable: bool = False

    @computed_field
    @property
    def cdn_prefix(self) -> str:
        return f"{self.api_prefix}/hmm/v{self.base_version}"

    @model_validator(mode="after")
    def check_default_version(self):
        assert self.base_version in self.versions
        return self


class AuthSettings(BaseSettings):
    max_age: int = Field(
        24 * 3600,
        ge=60,
        description=(
            "Indicates the number of seconds until the cookie expires."
        ),
    )

    key: str = Field(
        'U8@8BWw7S2xVwmZ4a!zn3Jw@eSAVf:t5Z6Dul"(/\Kjd}0hfNlG4kB£-E&"@16NCi"`_+*',  # noqa # type: ignore
        min_length=16,
        max_length=512,
        description="Fernet key",
    )
    jwt_key: str = Field(
        "$eckey", min_length=1, max_length=32, description="Fernet key"
    )
    jwt_secret: str = (
        "36EEdevj5af6WDVbrtBuubLtkH3CqPkm#2xCY7ZWS0dNQ6emsm8MXyzGKXa41bC6"
    )
    jwt_algorithm: str = "HS256"

    @computed_field
    @property
    def salt(self) -> str:
        from passlib.hash import bcrypt

        rseed = random.random()
        h = self.key.encode()
        random.seed(h)
        t_str = "".join(
            random.choices(
                "asdfghjklzxcvbnmqwertyuiopASDFGHJKLZCXVBNMQWERTYUIOP1234567890",  # noqa # type: ignore
                k=22,
            )
        )
        r = bcrypt.normhash(t_str)
        random.seed(rseed)
        return r

    @computed_field
    @property
    def real_key(self) -> bytes:
        b = self.jwt_key.encode("utf-8")
        while len(b) < 32:
            b += b + b"1"
        return base64.urlsafe_b64encode(b[:32])

    class Config:
        env_prefix = "auth_"


class Settings(BaseSettings):
    app: App = Field(default_factory=App)
    logging: Logging = Field(default_factory=Logging)
    db: DbSettings = Field(default_factory=DbSettings)
    api: Api = Field(default_factory=Api)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    MEDIA_DIR: Path = Path("./media")
    INTERNAL_MEDIA_DIR: Path = Path("./internal_media")

    @property
    def uvicorn_kwargs(self) -> dict:
        result = self.app.model_dump(include={"host", "port", "workers"})
        return result

    @property
    def debug(self) -> bool:
        return self.logging.level == "DEBUG"


class AlembicSettings(BaseSettings):
    db: DbSettings = Field(default_factory=DbSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)


LOGGER_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<yellow>{process}</yellow> | "
    "<level>{level: ^7}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)


def init_logger(log_level: str, log_path: str | None):
    logger.remove()

    logger.add(
        sys.stderr, colorize=True, format=LOGGER_FORMAT, level=log_level
    )
    if log_path:
        logger.add(
            log_path,
            level=log_level,
            format=LOGGER_FORMAT,
            rotation="1 week",
            retention=4,
            compression="zip",
            serialize=True,
        )


@cache
def get_settings():
    if (env_settings := EnvSettings()).ignore:
        dotenv_path = None
    elif env_settings.is_env_path_abs:
        dotenv_path = env_settings.name
    else:
        dotenv_path = find_dotenv(env_settings.name)
    load_dotenv(dotenv_path)
    if "alembic" in sys.argv[0]:
        return AlembicSettings()
    _settings = Settings()
    init_logger(_settings.logging.level, _settings.logging.log_path)
    return _settings
