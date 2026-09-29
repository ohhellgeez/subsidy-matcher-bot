import json

import redis

from ..config import Settings

TTL = 60 * 60 * 24
_settings = Settings.from_env()


def new_session() -> dict:
    return {
        "state": "START",
        "data": {},
        "history": [],
        "matches": [],
        "current_detail_id": None,
        "editing_field": None,
    }


class SessionStore:
    def __init__(self):
        try:
            self._r = redis.Redis.from_url(_settings.redis_url, decode_responses=True)
            self._r.ping()
        except Exception:
            self._r = None  
        self._mem: dict[str, dict] = {}

    def get(self, user_id: str) -> dict:
        if self._r:
            raw = self._r.get(f"session:{user_id}")
            return json.loads(raw) if raw else new_session()
        return self._mem.get(user_id) or new_session()

    def save(self, user_id: str, session: dict) -> None:
        if self._r:
            self._r.set(f"session:{user_id}", json.dumps(session, ensure_ascii=False), ex=TTL)
        else:
            self._mem[user_id] = session