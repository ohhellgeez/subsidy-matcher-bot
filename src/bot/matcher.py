from .db import get_session
from database.models import SupportMeasure
from datetime import datetime


def _split(value: str | None) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def _prefix_match(a: str, b: str) -> bool:
    return a.startswith(b) or b.startswith(a)


def _opf_ok(req_opf, company_opf) -> bool:
    allowed = _split(req_opf)
    if not allowed or not company_opf:
        return not allowed
    return company_opf in allowed


def _okwed_ok(req_okwed, not_okwed, company_okwed) -> bool:
    if not company_okwed:
        return True
    if any(_prefix_match(company_okwed, c) for c in _split(not_okwed)):
        return False
    allowed = _split(req_okwed)
    if not allowed:
        return True
    return any(_prefix_match(company_okwed, c) for c in allowed)


def _region_ok(req_okato, company_okato) -> bool:
    if not req_okato or req_okato == "0":
        return True
    return company_okato == req_okato


def _employees_ok(req_min, req_max, count) -> bool:
    if count is None:
        return True
    if req_min is not None and count < req_min:
        return False
    if req_max is not None and count > req_max:
        return False
    return True


def _exist_term_ok(req_min, months) -> bool:
    if req_min is None or months is None:
        return True
    return months >= req_min


def match(query_profile: dict) -> list[dict]:
    with get_session() as session:
        measures = session.query(SupportMeasure).filter(SupportMeasure.active == 1).all()
        result = []
        for m in measures:
            req = m.requirements
            if req is None:
                continue
            if not _opf_ok(req.opf, query_profile.get("opf")):
                continue
            if not _okwed_ok(req.okwed, req.not_okwed, query_profile.get("okwed")):
                continue
            if not _region_ok(req.okato, query_profile.get("region_okato")):
                continue
            if not _employees_ok(req.min_empl_amount, req.max_empl_amount,
                                  query_profile.get("employees_count")):
                continue
            if not _exist_term_ok(req.min_exist_term, query_profile.get("exist_term_months")):
                continue

            score = 100
            
            amount = m.support_amount_till or m.support_amount_from or 0
            score += min(50, amount // 100000)
            
            if m.end_date:
                days_left = (m.end_date - datetime.now()).days
                if 0 <= days_left <= 30:
                    score += 30

            result.append({
                "id": m.id,
                "name": m.name,
                "score": score,
                "short_description": m.short_description,
                "support_amount_from": m.support_amount_from,
                "support_amount_till": m.support_amount_till,
                "end_date": m.end_date,
                "recipient_category": m.recipient_category,
                "link": m.documents[0].link if m.documents else "—",
            })
            
        result.sort(key=lambda x: x["score"], reverse=True)
        return result