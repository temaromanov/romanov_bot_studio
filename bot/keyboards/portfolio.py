from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.constants.services import SERVICE_ID_TO_TITLE


def portfolio_services_kb() -> InlineKeyboardMarkup:
    # inline-меню услуг для портфолио
    rows: list[list[InlineKeyboardButton]] = []
    for service_id, title in SERVICE_ID_TO_TITLE.items():
        rows.append([InlineKeyboardButton(text=title, callback_data=f"portfolio:open:{service_id}")])

    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="portfolio:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def portfolio_after_album_kb(service_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Оставить заявку", callback_data=f"portfolio:apply:{service_id}")],
            [InlineKeyboardButton(text="⬅️ Назад к списку услуг", callback_data="portfolio:list")],
        ]
    )
