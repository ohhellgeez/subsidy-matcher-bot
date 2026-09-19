"""Конфигурация приложения, читаемая из переменных окружения.

Все значения имеют безопасные значения по умолчанию, поэтому приложение
поднимается даже без файла ``.env`` (кроме обязательного ``MAX_BOT_TOKEN``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

DEFAULT_BASE_URL = "https://platform-api2.max.ru"


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    # --- API МАХ ---
    max_bot_token: str = ""
    max_base_url: str = DEFAULT_BASE_URL
    max_request_timeout: int = 30

    # --- Режим доставки: "polling" | "webhook" ---
    mode: str = "polling"

    # --- Long Polling ---
    polling_timeout: int = 30
    polling_limit: int = 100
    polling_event_types: list[str] = field(default_factory=list)

    # --- Webhook ---
    webhook_url: str = ""
    webhook_secret: str = ""
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8000
    webhook_path: str = "/webhook"

    # --- PostgreSQL ---
    postgres_user: str = "myuser"
    postgres_password: str = "mypassword"
    postgres_db: str = "max_db"
    postgres_host: str = "db"
    postgres_port: int = 5432

    # --- Redis ---
    redis_host: str = "redis"
    redis_port: int = 6379

    @property
    def postgres_dsn(self) -> str:
        """SQLAlchemy DSN для подключения к PostgreSQL."""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def webhook_enabled(self) -> bool:
        return self.mode == "webhook"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            max_bot_token=os.getenv("MAX_BOT_TOKEN", "").strip(),
            max_base_url=os.getenv("MAX_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            max_request_timeout=_env_int("MAX_REQUEST_TIMEOUT", 30),
            mode=os.getenv("BOT_MODE", "polling").strip().lower(),
            polling_timeout=_env_int("POLLING_TIMEOUT", 30),
            polling_limit=_env_int("POLLING_LIMIT", 100),
            polling_event_types=[
                item.strip()
                for item in os.getenv("POLLING_EVENT_TYPES", "").split(",")
                if item.strip()
            ],
            webhook_url=os.getenv("WEBHOOK_URL", "").strip(),
            webhook_secret=os.getenv("WEBHOOK_SECRET", "").strip(),
            webhook_host=os.getenv("WEBHOOK_HOST", "0.0.0.0").strip(),
            webhook_port=_env_int("WEBHOOK_PORT", 8000),
            webhook_path=os.getenv("WEBHOOK_PATH", "/webhook").strip(),
            postgres_user=os.getenv("POSTGRES_USER", "myuser").strip(),
            postgres_password=os.getenv("POSTGRES_PASSWORD", "mypassword").strip(),
            postgres_db=os.getenv("POSTGRES_DB", "max_db").strip(),
            postgres_host=os.getenv("POSTGRES_HOST", "db").strip(),
            postgres_port=_env_int("POSTGRES_PORT", 5432),
            redis_host=os.getenv("REDIS_HOST", "redis").strip(),
            redis_port=_env_int("REDIS_PORT", 6379),
        )

    def validate(self) -> None:
        """Проверяет обязательные параметры; бросает ``ValueError`` при проблемах."""
        if not self.max_bot_token:
            raise ValueError(
                "MAX_BOT_TOKEN не задан. Скопируйте .env.example в .env и укажите токен."
            )
        if self.mode not in {"polling", "webhook"}:
            raise ValueError(f"Неизвестный BOT_MODE: {self.mode!r} (ожидается polling или webhook)")
        if self.webhook_enabled and not self.webhook_url.startswith("https://"):
            raise ValueError("WEBHOOK_URL должен начинаться с https:// (МАХ требует HTTPS).")

