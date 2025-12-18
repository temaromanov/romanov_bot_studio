from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def page_actions_kb(back_text: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Оставить заявку", callback_data="lead:start")],
            [InlineKeyboardButton(text=back_text, callback_data="pages:back_menu")],
        ]
    )
