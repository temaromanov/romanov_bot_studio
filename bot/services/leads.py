from __future__ import annotations

import json
from typing import Any


_DEADLINE_MAP: dict[str, str] = {
    "urgent": "Срочно",
    "week": "В течение недели",
    "not_urgent": "Не срочно",
}


def map_deadline(deadline_key: str, custom_text: str | None = None) -> str:
    """
    SPEC:
      urgent -> "Срочно"
      week -> "В течение недели"
      not_urgent -> "Не срочно"
      custom -> custom_text
    """
    key = (deadline_key or "").strip()
    if key == "custom":
        return (custom_text or "").strip() or "—"
    return _DEADLINE_MAP.get(key, "—")


def prepare_lead_data(
    *,
    tg_user_id: int,
    tg_username: str | None,
    tg_full_name: str,
    service: str,
    task: str,
    deadline_key: str,
    deadline_custom_text: str | None,
    budget: str | None,
    contact: str | None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    deadline_human = map_deadline(deadline_key, deadline_custom_text)

    payload = {
        "tg_user_id": tg_user_id,
        "tg_username": tg_username,
        "tg_full_name": tg_full_name,
        "service": service,
        "task": task,
        "deadline": deadline_human,
        "budget": budget,
        "contact": contact,
        "extra_json": json.dumps(extra or {}, ensure_ascii=False),
    }
    return payload
