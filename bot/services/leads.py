from __future__ import annotations

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
    key = (deadline_key or "").strip().removeprefix("deadline:")
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
        "extra_json": extra or {},
    }
    return payload


def format_admin_message(lead: dict[str, Any], files: list[dict[str, str]] | None = None) -> str:
    """Единый формат уведомления админу по SPEC."""

    username = lead.get("tg_username") or ""
    username_part = f" (@{username})" if username else ""

    lines = [
        "🆕 Новая заявка",
        f"От: {lead.get('tg_full_name')}{username_part}",
        f"Услуга: {lead.get('service')}",
        f"Задача: {lead.get('task')}",
        f"Срок: {lead.get('deadline')}",
        f"Контакт: {lead.get('contact')}",
    ]

    budget = lead.get("budget")
    if budget:
        lines.append(f"Бюджет: {budget}")

    files = files or []
    if files:
        lines.append("Файлы:")
        for f in files:
            ftype = (f.get("file_type") or "—").strip()
            fid = (f.get("file_id") or "—").strip()
            lines.append(f"- {ftype}: {fid}")

    return "\n".join(lines)
