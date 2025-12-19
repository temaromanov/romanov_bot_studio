from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

from bot.constants.portfolio import PORTFOLIO_MEDIA_FILE_IDS
from bot.constants.services import get_service_title
from bot.handlers.lead_flow import start_lead_with_service_id
from bot.keyboards.main import main_menu_kb
from bot.keyboards.portfolio import portfolio_after_album_kb, portfolio_services_kb

router = Router()


async def _show_portfolio_services(message: Message) -> None:
    await message.answer("Выберите услугу, чтобы посмотреть примеры работ:", reply_markup=portfolio_services_kb())


async def _send_album_for_service(message: Message, service_id: str) -> None:
    title = get_service_title(service_id)
    if not title:
        await message.answer("Не удалось определить услугу. Откройте «Примеры работ» заново.")
        return

    file_ids = PORTFOLIO_MEDIA_FILE_IDS.get(service_id) or []
    if not file_ids:
        await message.answer(f"{title}\n\n⚠️ Примеры работ пока не настроены (нет file_id).")
        await message.answer("⬅️ Вернуться к списку услуг:", reply_markup=portfolio_services_kb())
        return

    media = [InputMediaPhoto(media=fid) for fid in file_ids[:10]]  # безопасно, даже если больше
    await message.answer_media_group(media=media)

    await message.answer(
        "Хотите такой же результат?",
        reply_markup=portfolio_after_album_kb(service_id),
    )


# ====== ENTRY: reply-menu ======
@router.message(F.text == "🖼 Примеры работ")
async def portfolio_from_menu(message: Message) -> None:
    await _show_portfolio_services(message)


# ====== NAV: list/menu ======
@router.callback_query(F.data == "portfolio:list")
async def portfolio_list(call: CallbackQuery) -> None:
    await call.answer()
    await _show_portfolio_services(call.message)


@router.callback_query(F.data == "portfolio:menu")
async def portfolio_to_menu(call: CallbackQuery) -> None:
    await call.answer()
    await call.message.answer("Главное меню 👇", reply_markup=main_menu_kb())


# ====== OPEN SERVICE (album) ======
@router.callback_query(F.data.startswith("portfolio:open:"))
async def portfolio_open(call: CallbackQuery) -> None:
    service_id = (call.data or "").split(":", 2)[2].strip()
    await call.answer()
    await _send_album_for_service(call.message, service_id)


# ====== APPLY (start lead with selected service) ======
@router.callback_query(F.data.startswith("portfolio:apply:"))
async def portfolio_apply(call: CallbackQuery, state: FSMContext) -> None:
    service_id = (call.data or "").split(":", 2)[2].strip()
    await call.answer()
    await start_lead_with_service_id(call.message, state, service_id)
