import logging

from .config import Settings
from .max_client.client import MaxClient
from .max_client.models import Button, Update

from .bot.storage import SessionStore
from .bot.dispatcher import _advance, _render
from .bot.types import Reply

logger = logging.getLogger(__name__)

class BotHandler:
    """Маршрутизирует события Update и пропускает их через FSM."""

    def __init__(self, client: MaxClient, settings: Settings) -> None:
        self.client = client
        self.settings = settings
        self.store = SessionStore()

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
        if not user_id:
            return
            
        session = self.store.get(user_id)
        _advance(session, text="/start", callback=None)
        reply = _render(session)
        
        self.store.save(user_id, session)
        self._send_reply(user_id, reply)

    def _on_message(self, update: Update) -> None:
        user_id = update.user_id
        if not user_id:
            return
            
        text = update.text or ""
        logger.info("Сообщение от %s: %r", user_id, text)

        session = self.store.get(user_id)
        reply = _advance(session, text=text, callback=None)
        if not reply:
            reply = _render(session)
        
        self.store.save(user_id, session)
        self._send_reply(user_id, reply)

    def _on_callback(self, update: Update) -> None:
        user_id = update.user_id
        if not update.callback or not user_id:
            return
            
        payload = update.callback.payload or update.callback.callback_id
        logger.info("Callback payload=%r user_id=%s", payload, user_id)

        session = self.store.get(user_id)
        
        reply = _advance(session, text=None, callback=payload)
        if not reply:
            reply = _render(session)
        
        self.store.save(user_id, session)
        self._send_reply(user_id, reply)

    def _send_reply(self, user_id: str, reply: Reply | None) -> None:
        if not reply:
            return
            
        if reply.buttons:
            rows = []
            for text, payload in reply.buttons:
                if payload.startswith("http://") or payload.startswith("https://"):
                    rows.append([Button.link(text, payload)])
                else:
                    rows.append([Button.callback(text, payload)])
            self.client.send_keyboard(user_id, reply.text, rows)
        else:
            self.client.send_text(user_id, reply.text)
