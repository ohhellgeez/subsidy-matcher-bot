OPF_MAP = {
    "ИП": "individual",
    "ООО": "legal",
    "Самозанятый": "self",
    "КФХ": "physical", 
}

INDUSTRY_OKWED_PREFIX = {
    "Сельское хозяйство": "01",
    "Промышленность": "10",
    "Торговля": "47",
    "Услуги": "62",
    "Другое": None,
}

REGIONS = [
    {"name": "Москва", "okato": "45000000000"},
    {"name": "Алтайский край", "okato": "01000000000"},
    {"name": "Республика Татарстан", "okato": "92000000000"},
]
REGION_NAMES = [r["name"] for r in REGIONS]
OKATO_BY_NAME = {r["name"]: r["okato"] for r in REGIONS}
NAME_BY_OKATO = {r["okato"]: r["name"] for r in REGIONS}


def _employees_count(data: dict) -> int | None:
    if "employees_count" in data:  
        return data["employees_count"]
    has = data.get("has_employees")
    if has == "Нет":
        return 0
    return None 
def build_query_profile(data: dict) -> dict:
    """Анкета/данные по ИНН -> поля для сопоставления с measure_requirements."""
    return {
        "opf": data.get("opf") or OPF_MAP.get(data.get("entity_type")),
        "okwed": data.get("okwed") or INDUSTRY_OKWED_PREFIX.get(data.get("industry")),
        "region_okato": data.get("region_okato") or OKATO_BY_NAME.get(data.get("region")),
        "employees_count": _employees_count(data),
        "exist_term_months": data.get("exist_term_months"),
    }