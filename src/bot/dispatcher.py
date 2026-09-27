import logging

from .catalog import build_query_profile
from .matcher import match
from .render import (
    NAV, after_link_reply, ask_inn_reply, ask_name_reply, change_menu_reply,
    details_reply, inn_not_found_reply, prompt_reply, results_list_reply,
    summary_reply, welcome_reply,
)
from .steps import NEXT_STATE, STEP_BY_FIELD, STEP_BY_STATE, parse_value
from .storage import SessionStore, new_session
from .types import Reply
from .validators import lookup_inn, valid_inn, valid_name

log = logging.getLogger(__name__)
store = SessionStore()


def _goto(session: dict, state: str) -> None:
    session["history"].append(session["state"])
    session["state"] = state


def _find_match(session: dict) -> dict | None:
    mid = session.get("current_detail_id")
    for m in session.get("matches", []):
        if m["id"] == mid:
            return m
    return None


def _advance(session: dict, text: str | None, callback: str | None) -> Reply | None:
    text = (text or "").strip()
    state = session["state"]

    if callback == "restart" or text.lower() in ("/start", "начать заново"):
        session.update(new_session())
        return None
    if callback == "retry":
        return None
    if callback == "back":
        if session["history"]:
            session["state"] = session["history"].pop()
        return None

    if state == "START":
        if callback == "begin":
            _goto(session, "ASK_NAME")
        return None

    if state == "ASK_NAME":
        if callback == "skip_name":
            _goto(session, "ASK_INN")
            return None
        if text:
            name = valid_name(text)
            if name is None:
                return ask_name_reply(error="Введите имя буквами, от 2 до 40 символов.")
            session["data"]["name"] = name
            _goto(session, "ASK_INN")
            return None
        return ask_name_reply(error="Напишите, как к вам обращаться, или нажмите «Пропустить».")

    if state == "ASK_INN":
        if callback == "manual":
            _goto(session, "ASK_REGION")
            return None
        if text:
            if not valid_inn(text):
                return ask_inn_reply(session["data"].get("name"),
                                      error="ИНН должен содержать 10 или 12 цифр.")
            found = lookup_inn(text)
            if not found:
                return inn_not_found_reply()
            session["data"]["inn"] = text
            session["data"].update(found)
            _goto(session, "PROCESSING")
            return None
        return ask_inn_reply(session["data"].get("name"),
                              error="Отправьте ИНН текстом или нажмите «Ввести вручную».")

    if state in STEP_BY_STATE:
        step = STEP_BY_STATE[state]
        value = None
        if callback and callback.startswith("ans:"):
            value = parse_value(step, callback[4:])
        elif text:
            value = parse_value(step, text)
        if value is None:
            return prompt_reply(step, error=f"Не понял ответ. {step['hint']}")
        session["data"][step["field"]] = value
        if session.get("editing_field"):
            session["editing_field"] = None
            _goto(session, "PROCESSING")
        else:
            _goto(session, NEXT_STATE.get(state, "PROCESSING"))
        return None

    if state == "SUMMARY":
        if callback == "show":
            _goto(session, "RESULTS_LIST")
        return None

    if state == "RESULTS_LIST":
        if callback and callback.startswith("details:"):
            session["current_detail_id"] = callback.split(":", 1)[1]
            _goto(session, "DETAILS")
            return None
        if callback == "download":
            return Reply("Скачивание подборки в виде файла скоро будет доступно.", NAV)
        return None

    if state == "DETAILS":
        if callback and callback.startswith("link:"):
            _goto(session, "AFTER_LINK")
        elif callback == "back_to_list":
            session["state"] = "RESULTS_LIST"
        return None

    if state == "AFTER_LINK":
        if callback == "back_to_list":
            session["state"] = "RESULTS_LIST"
        elif callback == "change":
            _goto(session, "CHANGE_MENU")
        return None

    if state == "CHANGE_MENU":
        if callback and callback.startswith("change_field:"):
            field = callback.split(":", 1)[1]
            session["editing_field"] = field
            _goto(session, STEP_BY_FIELD[field]["state"])
        return None

    return None


def _render(session: dict) -> Reply:
    state = session["state"]
    name = session["data"].get("name")

    if state == "START":
        return welcome_reply()
    if state == "ASK_NAME":
        return ask_name_reply()
    if state == "ASK_INN":
        return ask_inn_reply(name)
    if state == "PROCESSING":
        query_profile = build_query_profile(session["data"])
        matches = match(query_profile)