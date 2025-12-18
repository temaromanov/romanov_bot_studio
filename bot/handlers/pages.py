from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.keyboards.main import main_menu_kb
from bot.keyboards.pages import page_actions_kb
from bot.texts.static_pages import CONTACTS_TEXT, HOW_WE_WORK_TEXT

router = Router()


@router.message(F.text == "🧾 Как мы работаем")
async def how_we_work(message: Message) -> None:
    await message.answer(HOW_WE_WORK_TEXT, reply_markup=page_actions_kb("⬅️ Назад"))


@router.message(F.text == "☎️ Контакты")
async def contacts(message: Message) -> None:
    await message.answer(CONTACTS_TEXT, reply_markup=page_actions_kb("⬅️ В меню"))


@router.callback_query(F.data == "pages:back_menu")
async def pages_back_menu(call: CallbackQuery) -> None:
    await call.message.answer("Главное меню 👇", reply_markup=main_menu_kb())
    await call.answer()
