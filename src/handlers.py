"""Диспетчер входящих событий бота.

Этот модуль — «шов» между коннектором API МАХ (Роль 1) и бизнес-логикой
анкетирования/FSM (Роли 3 и 4). Реализация ``_on_message`` / ``_on_callback``
заменяется командой по мере готовности движка сопоставления и стейт-машины.
"""

from __future__ import annotations

import json
import logging

from .config import Settings
from .max_client.client import MaxClient
from .max_client.models import Button, Update

logger = logging.getLogger(__name__)

# Текст приветствия при старте диалога.
_WELCOME_TEXT = (
    "Здравствуйте! Я помогу подобрать меры поддержки для вашего бизнеса.\n"
    "Я задам несколько коротких вопросов (регион, форма бизнеса, отрасль, "
    "наличие сотрудников) и покажу подходящие субсидии, гранты и льготы."
)

# Кнопка запуска анкеты (показывается на старте и на любое текстовое сообщение).
_START_ROWS = [[Button.callback("Начать подбор", "start_questionnaire")]]


class BotHandler:
    """Маршрутизирует события ``Update`` и отвечает пользователю."""

    def __init__(self, client: MaxClient, settings: Settings) -> None:
        self.client = client
        self.settings = settings

    def handle(self, update: Update) -> None:
        """Точка входа для всех событий."""
        handler = {
            "bot_started": self._on_start,
            "message_created": self._on_message,
            "message_callback": self._on_callback,
        }.get(update.update_type)
        if handler is None:
            logger.debug("Пропуск события %s", update.update_type)
            return
        handler(update)

    def _on_start(self, update: Update) -> None:
        user_id = update.user_id
        if user_id is None:
            logger.warning("bot_started без user_id")
            return
        self.client.send_keyboard(user_id, _WELCOME_TEXT, _START_ROWS)

    def _on_message(self, update: Update) -> None:
        user_id = update.user_id
        if user_id is None:
            logger.warning("message_created без user_id")
            return
        text = update.text or ""
        logger.info("Сообщение от %s: %r", user_id, text)

        # TODO(Роль 4 — Bot Flow & FSM): здесь подключается стейт-машина (Redis)
        # и движок сопоставления (Роль 3). Пока возвращаем приветствие с кнопкой.
        self.client.send_keyboard(user_id, _WELCOME_TEXT, _START_ROWS)

    def _on_callback(self, update: Update) -> None:
        logger.info("Callback raw: %s", json.dumps(update.raw, ensure_ascii=False))
        if update.callback is None or update.user_id is None:
            logger.warning("message_callback без callback/user")
            return
        payload = update.callback.payload or update.callback.callback_id
        logger.info("Callback payload=%r user_id=%s", payload, update.user_id)

        # ВАЖНО: не используем answer_callback с `message`, т.к. это заменяет
        # исходное сообщение (и кнопку). Отправляем НОВОЕ сообщение.
        # TODO(Роль 4): маршрутизация ответов кнопок анкеты.
        if payload == "start_questionnaire":
            rows = [
                [Button.callback("Регион А", "region=A"), Button.callback("Регион Б", "region=B")],
            ]
            self.client.send_keyboard(update.user_id, "Вопрос 1/4: выберите регион", rows)
        else:
            self.client.send_text(update.user_id, f"Вы нажали: {payload}")
