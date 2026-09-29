from .catalog import REGION_NAMES
from .validators import parse_region

STEPS = [
    {
        "state": "ASK_REGION",
        "field": "region",
        "question": "Укажите ваш регион.\nЭто поможет подобрать актуальные меры поддержки.",
        "options": REGION_NAMES[:4],
        "parse": parse_region,
        "hint": "Выберите регион кнопкой или напишите название текстом.",
        "change_label": "Регион",
    },
    {
        "state": "ASK_ENTITY",
        "field": "entity_type",
        "question": "Уточните форму бизнеса:",
        "options": ["ИП", "ООО", "Самозанятый", "КФХ"],
        "hint": "Выберите один из вариантов кнопкой.",
        "change_label": "Форма бизнеса",
    },
    {
        "state": "ASK_INDUSTRY",
        "field": "industry",
        "question": "Укажите отрасль деятельности:",
        "options": ["Сельское хозяйство", "Промышленность", "Торговля", "Услуги", "Другое"],
        "hint": "Выберите один из вариантов кнопкой.",
        "change_label": "Отрасль",
    },
    {
        "state": "ASK_EMPLOYEES",
        "field": "has_employees",
        "question": "Есть ли у вас наёмные сотрудники?\nЭто поможет точнее подобрать меры поддержки.",
        "options": ["Да", "Нет"],
        "hint": "Ответьте «Да» или «Нет».",
        "change_label": "Сотрудники",
    },
]

for i, s in enumerate(STEPS, 1):
    s["index"] = i

STEP_BY_STATE = {s["state"]: s for s in STEPS}
STEP_BY_FIELD = {s["field"]: s for s in STEPS}

ORDER = [s["state"] for s in STEPS]
NEXT_STATE = {a: b for a, b in zip(ORDER, ORDER[1:])}


def parse_value(step: dict, text: str):
    t = text.strip()
    if step.get("parse"):
        return step["parse"](t)
    for opt in step["options"]:
        if t.lower() == opt.lower():
            return opt
    return None