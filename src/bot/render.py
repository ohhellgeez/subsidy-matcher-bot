from .steps import STEPS
from .types import Reply

NAV = [("← Назад", "back"), ("Начать заново", "restart")]

RECIPIENT_LABELS = {
    "micro": "микропредприятия", "small": "малый бизнес",
    "medium": "средний бизнес", "other": "прочие",
}


def _format_amount(m: dict) -> str:
    frm, till = m.get("support_amount_from"), m.get("support_amount_till")
    if not frm and not till:
        return "не указан"
    if frm and till:
        return f"от {frm:,} до {till:,} ₽".replace(",", " ")
    return f"до {till:,} ₽".replace(",", " ") if till else f"от {frm:,} ₽".replace(",", " ")


def _format_deadline(m: dict) -> str:
    d = m.get("end_date")
    return d.strftime("%d.%m.%Y") if d else "без срока"


def _format_recipients(m: dict) -> str:
    cats = (m.get("recipient_category") or "").split(",")
    labels = [RECIPIENT_LABELS.get(c.strip(), c.strip()) for c in cats if c.strip()]
    return ", ".join(labels) if labels else "не указано"


def welcome_reply() -> Reply:
    return Reply(
        "Здравствуйте! Я помогу найти субсидии, гранты и льготы для вашего бизнеса.\n"
        "Ответьте на несколько вопросов, чтобы я подобрал подходящие меры.",
        [("Начать", "begin")],
    )


def ask_name_reply(error: str | None = None) -> Reply:
    head = f"{error}\n\n" if error else ""
    text = f"{head}Как я могу к вам обращаться?"
    return Reply(text, [("Пропустить", "skip_name")] + NAV)


def ask_inn_reply(error: str | None = None) -> Reply:
    head = f"{error}\n\n" if error else ""
    text = f"{head}Введите ваш ИНН, и я подберу актуальные меры поддержки автоматически."
    return Reply(text, [("Подобрать по анкете", "manual")] + NAV)

def inn_not_found_reply() -> Reply:
    text = (
        "ИНН не найден в базе.\n"
        "Введите корректный ИНН ещё раз или перейдите к ручному вводу."
    )
    return Reply(text, [("Ввести вручную", "manual")] + NAV)


def prompt_reply(step: dict, error: str | None = None) -> Reply:
    head = f"{error}\n\n" if error else ""
    text = f"{head}Шаг {step['index']} из {len(STEPS)}\n{step['question']}"
    buttons = [(o, f"ans:{o}") for o in step["options"]] + NAV
    return Reply(text, buttons)


def summary_reply(count: int, company_name: str | None = None) -> Reply:
    prefix = f"🏢 Организация: {company_name}\n" if company_name else ""
    if count == 0:
        return Reply(f"{prefix}Анализ завершён. Подходящих мер поддержки не нашлось.", NAV)
    text = f"{prefix}✅ Анализ завершён! Найдено подходящих мер поддержки: {count}."
    return Reply(text, [("Показать результаты", "show")] + NAV)


def results_list_reply(matches: list[dict], name: str | None = None) -> Reply:
    if not matches:
        return Reply("К сожалению, подходящих мер не нашлось.", NAV)
    
    lines = ["Ваши меры поддержки:\n"]
    buttons = []
    for i, m in enumerate(matches[:5], 1):
        lines.append(f"{i}. {m['name']} (рейтинг: {m['score']})")
        buttons.append((f"🔎 Изучить меру №{i}", f"details:{m['id']}"))
        
    buttons += [("Скачать подборку", "download")] + NAV
    return Reply("\n".join(lines), buttons)


def details_reply(m: dict) -> Reply:
    text = (
        f"{m['name']}\n"
        f"{m.get('short_description', '')}\n\n"
        f"Размер: {_format_amount(m)}\n"
        f"Срок подачи: {_format_deadline(m)}\n"
        f"Кто может получить: {_format_recipients(m)}\n\n"
        f"Ссылка: {m['link']}"
    )
    buttons = [("Открыть ссылку", m['link'])] + NAV
    return Reply(text, buttons)


def download_reply(matches: list[dict]) -> Reply:
    if not matches:
        return Reply("Список пуст.", NAV)
        
    lines = ["📄 Ваша подборка мер поддержки:\n"]
    for i, m in enumerate(matches, 1):
        lines.append(f"{i}. {m['name']}")
        lines.append(f"Размер: {_format_amount(m)}")
        lines.append(f"Ссылка: {m['link']}\n")
        
    text = "\n".join(lines) + "Вы можете скопировать или переслать это сообщение."
    return Reply(text, NAV)

def after_link_reply() -> Reply:
    text = "Хотите подобрать ещё меры или изменить параметры?"
    return Reply(text, [("Ещё меры", "back_to_list"), ("Изменить параметры", "change")] + NAV)


def change_menu_reply() -> Reply:
    buttons = [(s["change_label"], f"change_field:{s['field']}") for s in STEPS] + NAV
    return Reply("Что хотите изменить?", buttons)
