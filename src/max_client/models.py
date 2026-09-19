"""Модели данных API МАХ (объекты User, Message, Update, кнопки)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class User:
    """Пользователь или бот (объект ``User`` из документации МАХ)."""

    user_id: int
    first_name: str = ""
    last_name: Optional[str] = None
    username: Optional[str] = None
    is_bot: bool = False

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]]) -> Optional["User"]:
        if not data:
            return None
        return cls(
            user_id=int(data.get("user_id") or 0),
            first_name=str(data.get("first_name") or ""),
            last_name=data.get("last_name"),
            username=data.get("username"),
            is_bot=bool(data.get("is_bot")),
        )


@dataclass
class MessageBody:
    """Содержимое сообщения: текст и вложения (объект ``MessageBody``)."""

    text: Optional[str] = None
    attachments: Optional[list[dict[str, Any]]] = None

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]]) -> Optional["MessageBody"]:
        if not data:
            return None
        return cls(text=data.get("text"), attachments=data.get("attachments"))


@dataclass
class Message:
    """Сообщение или пост (объект ``Message``)."""

    sender: Optional[User] = None
    recipient: Optional[dict[str, Any]] = None
    timestamp: Optional[int] = None
    body: Optional[MessageBody] = None
    url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]]) -> Optional["Message"]:
        if not data:
            return None
        return cls(
            sender=User.from_dict(data.get("sender")),
            recipient=data.get("recipient"),
            timestamp=data.get("timestamp"),
            body=MessageBody.from_dict(data.get("body")),
            url=data.get("url"),
        )


@dataclass
class Callback:
    """Нажатие кнопки (вложенный объект ``callback`` события ``message_callback``).

    ``callback_id`` — служебный идентификатор для ответа через ``POST /answers``.
    ``payload`` — бизнес-данные, заданные в кнопке при отправке.
    ``user`` — пользователь, нажавший кнопку.
    """

    callback_id: str = ""
    payload: Optional[str] = None
    user: Optional["User"] = None

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]]) -> Optional["Callback"]:
        if not data:
            return None
        return cls(
            callback_id=str(data.get("callback_id") or ""),
            payload=data.get("payload"),
            user=User.from_dict(data.get("user")),
        )


@dataclass
class Update:
    """Событие, приходящее через Webhook или Long Polling (объект ``Update``)."""

    update_type: str
    timestamp: Optional[int] = None
    chat_id: Optional[int] = None
    user: Optional[User] = None
    is_channel: bool = False
    message: Optional[Message] = None
    body: Optional[MessageBody] = None
    callback: Optional[Callback] = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Update":
        return cls(
            update_type=str(data.get("update_type") or ""),
            timestamp=data.get("timestamp"),
            chat_id=data.get("chat_id"),
            user=User.from_dict(data.get("user")),
            is_channel=bool(data.get("is_channel")),
            message=Message.from_dict(data.get("message")),
            body=MessageBody.from_dict(data.get("body")),
            callback=Callback.from_dict(data.get("callback")),
            raw=data,
        )

    @property
    def text(self) -> Optional[str]:
        """Текст сообщения/комментария, если он есть в этом событии."""
        if self.message is not None and self.message.body is not None:
            return self.message.body.text
        if self.body is not None:
            return self.body.text
        return None

    @property
    def user_id(self) -> Optional[int]:
        """Идентификатор пользователя, инициировавшего событие.

        Для ``message_callback`` пользователь лежит в ``callback.user``
        (верхнеуровневого ``user`` в таких событиях нет).
        """
        if self.user is not None:
            return self.user.user_id
        if self.callback is not None and self.callback.user is not None:
            return self.callback.user.user_id
        if self.message is not None and self.message.sender is not None:
            return self.message.sender.user_id
        return None


@dataclass
class Button:
    """Кнопка inline-клавиатуры.

    Поддерживаемые типы (по документации МАХ):
    ``callback`` (с ``payload``), ``link`` (с ``url``), ``message``, ``clipboard``,
    ``request_contact``, ``request_geo_location``, ``open_app``.
    """

    text: str
    type: str = "callback"
    payload: Optional[str] = None
    url: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"type": self.type, "text": self.text}
        if self.payload is not None:
            data["payload"] = self.payload
        if self.url is not None:
            data["url"] = self.url
        return data

    @classmethod
    def callback(cls, text: str, payload: str) -> "Button":
        """Кнопка, порождающая событие ``message_callback`` с переданным ``payload``."""
        return cls(text=text, type="callback", payload=payload)

    @classmethod
    def link(cls, text: str, url: str) -> "Button":
        """Кнопка-ссылка."""
        return cls(text=text, type="link", url=url)


def inline_keyboard(rows: list[list[Button]]) -> dict[str, Any]:
    """Собирает объект ``inline_keyboard`` для поля ``attachments``.

    ``rows`` — список рядов; каждый ряд — список кнопок (до 7 в ряду).
    """
    return {
        "type": "inline_keyboard",
        "payload": {"buttons": [[button.to_dict() for button in row] for row in rows]},
    }
