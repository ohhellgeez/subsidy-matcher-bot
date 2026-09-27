"""Справочники: перевод ответов анкеты в реальные коды из models.py."""

# ПРОВЕРИТЬ с Ролью 2: "Фермерское хозяйство" отнесено к 'physical' по остаточному
# принципу (chk_company_opf разрешает individual/legal/physical/self/selfindividual).
OPF_MAP = {
    "ИП": "individual",
    "ООО": "legal",
    "Самозанятый": "self",
    "Фермерское хозяйство": "physical",
}

# ПРОВЕРИТЬ с Ролью 2 при появлении новых мер: сейчас в БД есть только коды 01.xx
# (сельхозтехника) и 62.xx (ИТ). "Услуги" временно указывает на раздел 62.
INDUSTRY_OKWED_PREFIX = {
    "Сельское хозяйство": "01",
    "Промышленность": "10",
    "Торговля": "47",
    "Услуги": "62",
    "Другое": None,
}

# Из regions.json — три региона, которые реально загружены в БД скриптом seed.py
REGIONS = [
    {"name": "Москва", "okato": "45000000000"},
    {"name": "Алтайский край", "okato": "01000000000"},
    {"name": "Республика Татарстан", "okato": "92000000000"},
]
REGION_NAMES = [r["name"] for r in REGIONS]
OKATO_BY_NAME = {r["name"]: r["okato"] for r in REGIONS}
NAME_BY_OKATO = {r["okato"]: r["name"] for r in REGIONS}


def _employees_count(data: dict) -> int | None:
    if "employees_count" in data:  # уже известно из БД по ИНН
        return data["employees_count"]
    has = data.get("has_employees")
    if has == "Нет":
        return 0
    return None  # "Да", но точное число не спрашивали — мягкий фильтр


def build_query_profile(data: dict) -> dict:
    """Анкета/данные по ИНН -> поля для сопоставления с measure_requirements."""
    return {
        "opf": data.get("opf") or OPF_MAP.get(data.get("entity_type")),
        "okwed": data.get("okwed") or INDUSTRY_OKWED_PREFIX.get(data.get("industry")),
        "region_okato": data.get("region_okato") or OKATO_BY_NAME.get(data.get("region")),
        "employees_count": _employees_count(data),
        "exist_term_months": data.get("exist_term_months"),
    }