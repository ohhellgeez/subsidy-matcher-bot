"""Коннектор к API чат-ботов платформы МАХ.

Экспортирует основные классы и функции для работы с API:
- ``MaxClient`` — HTTP-клиент (отправка сообщений, получение обновлений, вебхуки).
- ``Update``, ``Message``, ``User`` — модели данных API.
- ``Button`` / ``inline_keyboard`` — помощники для клавиатур.
"""

from .client import MaxClient
from .errors import (
    MaxAPIError,
    MaxAuthError,
    MaxConnectionError,
    MaxError,
    MaxRateLimitError,
)
from .models import (
    Button,
    Callback,
    Message,
    MessageBody,
    Update,
    User,
    inline_keyboard,
)

__all__ = [
    "MaxClient",
    "MaxError",
    "MaxAPIError",
    "MaxAuthError",
    "MaxConnectionError",
    "MaxRateLimitError",
    "Button",
    "Callback",
    "Message",
    "MessageBody",
    "Update",
    "User",
    "inline_keyboard",
]
