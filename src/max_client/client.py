"""HTTP-клиент для API чат-ботов МАХ.

Реализует минимально необходимый набор методов для чат-бота:
отправка сообщений, inline-клавиатуры, long polling, webhook-подписки
и ответы на нажатия кнопок (callback).

Документация API: https://dev.max.ru/docs-api
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional, Union

import requests

from .errors import (
    MaxAPIError,
    MaxAuthError,
    MaxConnectionError,
    MaxRateLimitError,
)
from .models import Button, Message, Update, inline_keyboard

logger = logging.getLogger(__name__)

# Максимум 2 сообщения в секунду в один диалог (требование платформы).
_MIN_SEND_INTERVAL = 0.55


class MaxClient:
    """Клиент API МАХ.

    Аутентификация выполняется заголовком ``Authorization: <token>``.
    """

    def __init__(
        self,
        token: str,
        base_url: str = "https://platform-api2.max.ru",
        timeout: int = 30,
        verify: Union[bool, str] = True,
    ) -> None:
        if not token:
            raise ValueError("token не может быть пустым")
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        # Платформа МАХ использует сертификаты Минцифры; при необходимости
        # сюда передаётся путь к CA-бандлу (см. MAX_CA_BUNDLE в .env).
        self._session.verify = verify
        self._session.headers.update(
            {
                "Authorization": token,
                "Content-Type": "application/json",
            }
        )
        self._last_send_ts = 0.0

    # ------------------------------------------------------------------ #
    # Низкоуровневый слой
    # ------------------------------------------------------------------ #
    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        try:
            response = self._session.request(
                method, url, params=params, json=json, timeout=self.timeout
            )
        except requests.RequestException as exc:
            raise MaxConnectionError(f"Сетевая ошибка при запросе {method} {path}: {exc}", exc) from exc

        if response.status_code == 401:
            raise MaxAuthError("Ошибка авторизации: токен неверный или отозван", status_code=401)
        if response.status_code == 429:
            raise MaxRateLimitError("Превышен лимит частоты запросов (429)", status_code=429)
        if response.status_code not in (200, 201, 202, 204):
            raise MaxAPIError(
                f"Ошибка API {method} {path}: HTTP {response.status_code}: {response.text}",
                status_code=response.status_code,
                payload=response.text,
            )

        if response.status_code == 204 or not response.content:
            return {}
        try:
            return response.json()
        except ValueError:
            return {}

    @staticmethod
    def _require_success(data: Any, operation: str) -> None:
        """Проверяет ответы вида ``{"success": bool, "message": str}``."""
        if isinstance(data, dict) and data.get("success") is False:
            raise MaxAPIError(
                f"{operation}: {data.get('message') or 'неизвестная ошибка'}",
                payload=data,
            )

    # ------------------------------------------------------------------ #
    # Информация о боте
    # ------------------------------------------------------------------ #
    def get_me(self) -> dict[str, Any]:
        """Возвращает информацию о боте (``GET /me``)."""
        return self._request("GET", "/me")

    # ------------------------------------------------------------------ #
    # Отправка сообщений
    # ------------------------------------------------------------------ #
    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_send_ts
        if elapsed < _MIN_SEND_INTERVAL:
            time.sleep(_MIN_SEND_INTERVAL - elapsed)
        self._last_send_ts = time.monotonic()

    def send_message(
        self,
        *,
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        text: Optional[str] = None,
        attachments: Optional[list[dict[str, Any]]] = None,
        text_format: Optional[str] = None,
        notify: Optional[bool] = None,
        disable_link_preview: Optional[bool] = None,
    ) -> Message:
        """Отправляет сообщение пользователю или в чат/канал (``POST /messages``)."""
        if user_id is None and chat_id is None:
            raise ValueError("Нужно указать user_id или chat_id")

        params: dict[str, Any] = {}
        if user_id is not None:
            params["user_id"] = user_id
        if chat_id is not None:
            params["chat_id"] = chat_id
        if disable_link_preview is not None:
            params["disable_link_preview"] = "true" if disable_link_preview else "false"

        body: dict[str, Any] = {}
        if text is not None:
            body["text"] = text
        if attachments is not None:
            body["attachments"] = attachments
        if text_format is not None:
            body["format"] = text_format
        if notify is not None:
            body["notify"] = notify

        self._throttle()
        data = self._request("POST", "/messages", params=params, json=body)
        return Message.from_dict(data) if isinstance(data, dict) else Message()

    def send_text(
        self,
        user_id: int,
        text: str,
        *,
        text_format: Optional[str] = None,
        notify: Optional[bool] = None,
    ) -> Message:
        """Удобная обёртка для отправки простого текстового сообщения."""
        return self.send_message(user_id=user_id, text=text, text_format=text_format, notify=notify)

    def send_keyboard(
        self,
        user_id: int,
        text: str,
        rows: list[list[Button]],
        *,
        notify: Optional[bool] = None,
    ) -> Message:
        """Отправляет сообщение с inline-клавиатурой."""
        return self.send_message(
            user_id=user_id,
            text=text,
            attachments=[inline_keyboard(rows)],
            notify=notify,
        )

    def edit_message(
        self,
        message_id: int,
        *,
        text: Optional[str] = None,
        attachments: Optional[list[dict[str, Any]]] = None,
        text_format: Optional[str] = None,
    ) -> Message:
        """Редактирует сообщение (``PUT /messages``)."""
        body: dict[str, Any] = {}
        if text is not None:
            body["text"] = text
        if attachments is not None:
            body["attachments"] = attachments
        if text_format is not None:
            body["format"] = text_format
        data = self._request("PUT", "/messages", params={"message_id": message_id}, json=body)
        return Message.from_dict(data) if isinstance(data, dict) else Message()

    # ------------------------------------------------------------------ #
    # Получение обновлений (Long Polling)
    # ------------------------------------------------------------------ #
    def get_updates(
        self,
        *,
        marker: Optional[int] = None,
        limit: int = 100,
        timeout: int = 30,
        types: Optional[list[str]] = None,
    ) -> tuple[list[Update], Optional[int]]:
        """Получает обновления через Long Polling (``GET /updates``).

        Возвращает кортеж ``(updates, next_marker)``.
        """
        params: dict[str, Any] = {"limit": limit, "timeout": timeout}
        if marker is not None:
            params["marker"] = marker
        if types:
            params["types"] = ",".join(types)

        data = self._request("GET", "/updates", params=params)
        if not isinstance(data, dict):
            return [], marker
        updates = [
            Update.from_dict(item) for item in data.get("updates", []) if isinstance(item, dict)
        ]
        next_marker = data.get("marker")
        return updates, next_marker

    # ------------------------------------------------------------------ #
    # Webhook
    # ------------------------------------------------------------------ #
    def subscribe_webhook(
        self,
        url: str,
        *,
        update_types: Optional[list[str]] = None,
        secret: Optional[str] = None,
    ) -> dict[str, Any]:
        """Подписывается на события через Webhook (``POST /subscriptions``)."""
        body: dict[str, Any] = {"url": url}
        if update_types:
            body["update_types"] = update_types
        if secret:
            body["secret"] = secret
        data = self._request("POST", "/subscriptions", json=body)
        self._require_success(data, "Подписка на webhook")
        return data

    def get_subscriptions(self) -> dict[str, Any]:
        """Возвращает текущие webhook-подписки (``GET /subscriptions``)."""
        return self._request("GET", "/subscriptions")

    def unsubscribe_webhook(self) -> dict[str, Any]:
        """Отписывается от webhook-обновлений (``DELETE /subscriptions``)."""
        data = self._request("DELETE", "/subscriptions")
        self._require_success(data, "Отписка от webhook")
        return data

    # ------------------------------------------------------------------ #
    # Callback (ответ на нажатие кнопки)
    # ------------------------------------------------------------------ #
    def answer_callback(
        self,
        callback_id: str,
        *,
        text: Optional[str] = None,
        rows: Optional[list[list[Button]]] = None,
        disable_link_preview: Optional[bool] = None,
    ) -> dict[str, Any]:
        """Отвечает на нажатие кнопки (``POST /answers``)."""
        params: dict[str, Any] = {"callback_id": callback_id}
        if disable_link_preview is not None:
            params["disable_link_preview"] = "true" if disable_link_preview else "false"

        body: dict[str, Any] = {}
        if text is not None or rows is not None:
            message: dict[str, Any] = {}
            if text is not None:
                message["text"] = text
            if rows is not None:
                message["attachments"] = [inline_keyboard(rows)]
            body["message"] = message

        self._throttle()
        data = self._request("POST", "/answers", params=params, json=body)
        self._require_success(data, "Ответ на callback")
        return data


