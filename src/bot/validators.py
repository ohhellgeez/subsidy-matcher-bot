import difflib
import re

from .catalog import REGION_NAMES
from .db import get_session
from ..database.models import Company, Region

NAME_PATTERN = re.compile(r"^[A-Za-zА-Яа-яЁё\- ]{2,40}$")


def valid_inn(inn: str) -> bool:
    if not inn.isdigit() or len(inn) not in (10, 12):
        return False

    def check(digits: str, weights: list[int]) -> int:
        return sum(int(d) * w for d, w in zip(digits, weights)) % 11 % 10

    if len(inn) == 10:
        return check(inn, [2, 4, 10, 3, 5, 9, 4, 6, 8]) == int(inn[9])
    return (
        check(inn, [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]) == int(inn[10])
        and check(inn, [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]) == int(inn[11])
    )


def lookup_inn(inn: str) -> dict | None:
    with get_session() as session:
        company = session.query(Company).filter_by(inn=inn).first()
        if not company:
            return None
        region = session.query(Region).filter_by(id=company.region_id).first()
        return {
            "company_name": company.name,
            "region": region.name if region else "вЂ”",
            "region_okato": region.okato if region else None,
            "opf": company.opf,
            "okwed": company.okwed,
            "employees_count": company.employees_count,
            "exist_term_months": company.exist_term_months,
        }


def parse_region(text: str) -> str | None:
    t = text.strip()
    for r in REGION_NAMES:
        if t.lower() == r.lower():
            return r
    close = difflib.get_close_matches(t.title(), REGION_NAMES, n=1, cutoff=0.7)
    return close[0] if close else None


def valid_name(text: str) -> str | None:
    t = text.strip()
    if NAME_PATTERN.match(t):
        return t.title()
    return None
