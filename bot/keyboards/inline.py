from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def services_kb(services: list[str]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for idx, title in enumerate(services, start=1):
        rows.append([InlineKeyboardButton(text=title, callback_data=f"svc:{idx}")])
    rows.append([InlineKeyboardButton(text="Отменить", callback_data="lead:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def deadline_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Срочно (1–2 дня)", callback_data="deadline:urgent"),
            ],
            [
                InlineKeyboardButton(text="В течение недели", callback_data="deadline:week"),
            ],
            [
                InlineKeyboardButton(text="Не срочно", callback_data="deadline:not_urgent"),
            ],
            [
                InlineKeyboardButton(text="Свой вариант", callback_data="deadline:custom"),
            ],
            [
                InlineKeyboardButton(text="Отменить", callback_data="lead:cancel"),
            ],
        ]
    )


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="lead:send"),
                InlineKeyboardButton(text="✏️ Изменить", callback_data="lead:edit"),
            ],
            [
                InlineKeyboardButton(text="❌ Отменить", callback_data="lead:cancel"),
            ],
        ]
    )
