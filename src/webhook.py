"""Webhook-сервер (FastAPI) для production-режима доставки событий.

Используется, когда ``BOT_MODE=webhook``. Принимает HTTPS POST-запросы
с объектом ``Update``, проверяет секрет в заголовке ``X-Max-Bot-Api-Secret``
и передаёт событие обработчику.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, Response

from .config import Settings
from .handlers import BotHandler
from .max_client.client import MaxClient
from .max_client.models import Update

logger = logging.getLogger(__name__)


def create_app(settings: Settings) -> FastAPI:
    client = MaxClient(
        settings.max_bot_token,
        base_url=settings.max_base_url,
        timeout=settings.max_request_timeout,
        verify=settings.max_ca_bundle or True,
    )
    handler = BotHandler(client, settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if settings.webhook_url:
            client.subscribe_webhook(
                settings.webhook_url,
                update_types=settings.polling_event_types or None,
                secret=settings.webhook_secret or None,
            )
            logger.info("Webhook-подписка создана: %s", settings.webhook_url)
        yield

    app = FastAPI(title="Subsidy Matcher Bot", version="0.1.0", lifespan=lifespan)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(settings.webhook_path)
    async def webhook(request: Request) -> Response:
        if settings.webhook_secret:
            if request.headers.get("X-Max-Bot-Api-Secret") != settings.webhook_secret:
                return Response(status_code=403)

        data = await request.json()
        update = Update.from_dict(data)
        try:
            handler.handle(update)
        except Exception:
            # Отвечаем 200, чтобы МАХ не повторял доставку; ошибка логируется.
            logger.exception("Ошибка обработки события %s", update.update_type)
        return Response(status_code=200)

    return app
