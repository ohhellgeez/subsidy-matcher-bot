"""Точка входа бота.

Выбор режима доставки управляется переменной окружения ``BOT_MODE``:
- ``polling`` (по умолчанию) — Long Polling через ``GET /updates``;
- ``webhook`` — HTTP-сервер (FastAPI) + подписка ``POST /subscriptions``.

Запуск: ``python -m src.main`` (из корня проекта).
"""

from __future__ import annotations

import logging
import time

from .config import Settings
from .handlers import BotHandler
from .max_client.client import MaxClient
from .max_client.errors import (
    MaxAPIError,
    MaxAuthError,
    MaxConnectionError,
    MaxRateLimitError,
)

logger = logging.getLogger(__name__)


def build_client(settings: Settings) -> MaxClient:
    return MaxClient(
        settings.max_bot_token,
        base_url=settings.max_base_url,
        timeout=settings.max_request_timeout,
        verify=settings.max_ca_bundle or True,
    )


def run_polling(settings: Settings) -> None:
    settings.validate()
    client = build_client(settings)
    handler = BotHandler(client, settings)

    logger.info("Запуск Long Polling (base_url=%s)", settings.max_base_url)
    marker: int | None = None

    while True:
        try:
            updates, marker = client.get_updates(
                marker=marker,
                limit=settings.polling_limit,
                timeout=settings.polling_timeout,
                types=settings.polling_event_types or None,
            )
            for update in updates:
                logger.info("Событие %s (user_id=%s)", update.update_type, update.user_id)
                try:
                    handler.handle(update)
                except MaxAuthError:
                    raise
                except Exception:
                    # Падение одного события не должно останавливать бота.
                    logger.exception("Ошибка обработки события %s", update.update_type)
        except MaxAuthError as exc:
            logger.error("Токен недействителен — остановка. %s", exc)
            break
        except MaxRateLimitError as exc:
            logger.warning("Превышен лимит: %s. Пауза 5 с.", exc)
            time.sleep(5)
        except (MaxConnectionError, MaxAPIError) as exc:
            logger.warning("Ошибка API: %s. Пауза 3 с.", exc)
            time.sleep(3)
        except KeyboardInterrupt:
            logger.info("Остановка по сигналу")
            break


def run_webhook(settings: Settings) -> None:
    settings.validate()
    import uvicorn

    from .webhook import create_app

    app = create_app(settings)
    logger.info(
        "Запуск Webhook на %s:%s%s",
        settings.webhook_host,
        settings.webhook_port,
        settings.webhook_path,
    )
    uvicorn.run(app, host=settings.webhook_host, port=settings.webhook_port)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = Settings.from_env()
    if settings.webhook_enabled:
        run_webhook(settings)
    else:
        run_polling(settings)


if __name__ == "__main__":
    main()

