"""Диспетчер входящих событий бота.

Этот модуль — «шов» между коннектором API МАХ (Роль 1) и бизнес-логикой
анкетирования/FSM (Роли 3 и 4). Реализация ``_on_message`` / ``_on_callback``
заменяется командой по мере готовности движка сопоставления и стейт-машины.
"""

from __future__ import annotations

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
        rows = [[Button.callback("Начать подбор", "start_questionnaire")]]
        self.client.send_keyboard(user_id, _WELCOME_TEXT, rows)

    def _on_message(self, update: Update) -> None:
        user_id = update.user_id
        if user_id is None:
            logger.warning("message_created без user_id")
            return
        text = update.text or ""
        logger.info("Сообщение от %s: %r", user_id, text)

        # TODO(Роль 4 — Bot Flow & FSM): здесь подключается стейт-машина
        # (Redis) и движок сопоставления (Роль 3). Пока — безопасный эхо-ответ,
        # чтобы бот был рабочим на всех этапах разработки.
        self.client.send_text(user_id, f"Получено: {text}")

    def _on_callback(self, update: Update) -> None:
        if update.callback is None:
            logger.warning("message_callback без callback")
            return
        payload = update.callback.callback_id
        logger.info("Callback %s (user_id=%s)", payload, update.user_id)

        # TODO(Роль 4): маршрутизация ответов кнопок анкеты.
        self.client.answer_callback(payload, text=f"Вы нажали: {payload}")
