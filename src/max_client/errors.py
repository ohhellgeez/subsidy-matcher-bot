"""Исключения коннектора API МАХ."""

from __future__ import annotations

from typing import Any, Optional


class MaxError(Exception):
    """Базовое исключение всех ошибок взаимодействия с API МАХ."""


class MaxConnectionError(MaxError):
    """Сетевая ошибка (не удалось достучаться до API)."""

    def __init__(self, message: str, original: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.original = original


class MaxAPIError(MaxError):
    """Ошибка API МАХ: неожиданный HTTP-статус или `success: false`."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        payload: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class MaxAuthError(MaxAPIError):
    """Ошибка авторизации (HTTP 401) — токен неверный или отозван."""


class MaxRateLimitError(MaxAPIError):
    """Превышен лимит частоты запросов (HTTP 429)."""
