from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.keyboards.main import main_menu_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    text = (
        "Привет! Это <b>Romanov Bot Studio</b>.\n"
        "Выберите пункт меню ниже 👇"
    )
    await message.answer(text, reply_markup=main_menu_kb())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = (
        "<b>Помощь</b>\n"
        "Используйте меню, чтобы посмотреть услуги и информацию.\n"
        "Если нужно связаться — откройте пункт «Контакты»."
    )
    await message.answer(text, reply_markup=main_menu_kb())


@router.message(F.text == "Услуги")
async def menu_services(message: Message) -> None:
    await message.answer(
        "Раздел «Услуги» — в разработке.\n"
        "Скоро тут появится выбор услуги и оформление заявки."
    )


@router.message(F.text == "Примеры работ")
async def menu_portfolio(message: Message) -> None:
    await message.answer(
        "Раздел «Примеры работ» — в разработке.\n"
        "Скоро добавим ссылки/кейсы."
    )


@router.message(F.text == "Как мы работаем")
async def menu_how_we_work(message: Message) -> None:
    await message.answer(
        "Раздел «Как мы работаем» — в разработке.\n"
        "Скоро добавим этапы, сроки и правила."
    )


@router.message(F.text == "Контакты")
async def menu_contacts(message: Message) -> None:
    await message.answer(
        "Контакты — в разработке.\n"
        "Скоро добавим удобные способы связи."
    )
