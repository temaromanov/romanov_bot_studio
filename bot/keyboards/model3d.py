from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def model3d_intro_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Дальше", callback_data="model3d:next")],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="lead:back_to_services"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="lead:cancel"),
            ],
        ]
    )
