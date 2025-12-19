from __future__ import annotations

from typing import Iterable, Union
from bot.constants.services import SERVICE_ID_TO_TITLE

# ===== Новый формат (dict по service_id) =====
PORTFOLIO_MEDIA_FILE_IDS: dict[str, list[str]] = {
    "neuro": [
        "AgACAgIAAxkBAAIBHmlD8RijmSgacFsTLtBKHnReFpeAAALCDWsbjoQgSkh3styFs-ebAQADAgADeQADNgQ",
        "AgACAgIAAxkBAAIBRGlD81RY8QABqELAqGDKgb7f8KW9RwACzw1rG46EIEp9swABDoS21RgBAAMCAAN5AAM2BA",
        "AgACAgIAAxkBAAIBRmlD83rUBI9C9u1PYO5_a1g4K-RgAALSDWsbjoQgSm6emFLU7-pkAQADAgADeQADNgQ",
        "AgACAgIAAxkBAAIBSGlD86YXbBxDPwABdkqW_2GBO8B_tQAC0w1rG46EIEoQda9g21u4tgEAAwIAA3kAAzYE",
        "AgACAgIAAxkBAAIBSmlD8-ucWbjvgAW117PitcuL8kpzAALVDWsbjoQgSqpkkC8kwrqEAQADAgADeQADNgQ",
    ],
    "restoration": [],
    "model3d": [],
    "content": [],
    "photo_stories": [],
    "video_greeting": [],
}

# ===== Старый формат (list по индексу) — НЕ УБИРАЕМ =====
PORTFOLIO_MEDIA: list[list[str]] = [
    PORTFOLIO_MEDIA_FILE_IDS.get(service_id, [])
    for service_id in SERVICE_ID_TO_TITLE.keys()
]


def is_configured(value: Union[str, Iterable[str]]) -> bool:
    """
    Совместимый багфикс.

    Принимает:
    - service_id (str)  -> смотрит в PORTFOLIO_MEDIA_FILE_IDS
    - file_ids (list)   -> проверяет, что список не пустой

    Нужно для старого services.py и нового portfolio.py
    """
    # Новый код
    if isinstance(value, str):
        return bool(PORTFOLIO_MEDIA_FILE_IDS.get(value) or [])

    # Старый код (file_ids list)
    try:
        return bool(list(value))
    except TypeError:
        return False
