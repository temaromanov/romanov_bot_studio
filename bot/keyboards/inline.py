from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def services_kb(services: list[str]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for idx, title in enumerate(services, start=1):
        rows.append([InlineKeyboardButton(text=title, callback_data=f"svc:{idx}")])
    rows.append([InlineKeyboardButton(text="Отменить", callback_data="lead:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def restoration_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🖼 Фото", callback_data="rest:photo"),
                InlineKeyboardButton(text="🎞 Видео", callback_data="rest:video"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="lead:back"),
                InlineKeyboardButton(text="Отменить", callback_data="lead:cancel"),
            ],
        ]
    )


def files_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Готово", callback_data="files:done"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="lead:back"),
                InlineKeyboardButton(text="Отменить", callback_data="lead:cancel"),
            ],
        ]
    )


def deadline_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔥 Срочно", callback_data="dl:urgent")],
            [InlineKeyboardButton(text="📅 В течение недели", callback_data="dl:week")],
            [InlineKeyboardButton(text="⏳ Не срочно", callback_data="dl:not_urgent")],
            [InlineKeyboardButton(text="✍️ Свой вариант", callback_data="dl:custom")],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="lead:back"),
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
                InlineKeyboardButton(text="⬅️ Назад", callback_data="lead:back"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="lead:cancel"),
            ],
        ]
    )
