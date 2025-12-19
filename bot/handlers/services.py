from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

from bot.constants.portfolio import PORTFOLIO_MEDIA, is_configured
from bot.constants.services import SERVICES
from bot.keyboards.inline import restoration_type_kb
from bot.keyboards.main import main_menu_kb
from bot.keyboards.model3d import model3d_intro_kb
from bot.keyboards.neuro import neuro_step1_kb
from bot.keyboards.services import service_card_kb, services_list_kb
from bot.keyboards.portfolio import portfolio_after_album_kb
from bot.states.lead_form import LeadForm
from bot.texts.neuro import NEURO_EXAMPLE_PHOTO_FILE_IDS, NEURO_STEP1_TEXT
from bot.texts.service_flows import MODEL3D_INTRO_TEXT
from bot.texts.services import SERVICE_CARDS_BY_TITLE

router = Router()


def _get_service_title(idx: int) -> str | None:
    if 1 <= idx <= len(SERVICES):
        return SERVICES[idx - 1]
    return None


def _is_restoration_service(title: str) -> bool:
    return "реставрац" in title.lower()


def _is_neuro_service(title: str) -> bool:
    return "нейрофотосесс" in title.lower()


def _is_content_service(title: str) -> bool:
    t = title.lower()
    return "контент" in t and "соц" in t


def _is_video_service(title: str) -> bool:
    return "видео" in title.lower() and "поздрав" in title.lower()


def _is_model3d_service(title: str) -> bool:
    t = title.lower()
    return "3d" in t and "модель" in t


@router.message(F.text == "🧩 Услуги")
async def services_entry(message: Message) -> None:
    await message.answer("Выберите услугу:", reply_markup=services_list_kb(SERVICES))


@router.callback_query(F.data == "services:back_menu")
async def services_back_menu(call: CallbackQuery) -> None:
    await call.message.answer("Главное меню 👇", reply_markup=main_menu_kb())
    await call.answer()


@router.callback_query(F.data == "services:list")
async def services_list(call: CallbackQuery) -> None:
    await call.message.answer("Выберите услугу:", reply_markup=services_list_kb(SERVICES))
    await call.answer()


@router.callback_query(F.data.startswith("services:open:"))
async def services_open(call: CallbackQuery) -> None:
    raw = (call.data or "").split(":", 2)[2]
    try:
        idx = int(raw)
    except ValueError:
        await call.answer("Некорректный выбор")
        return

    title = _get_service_title(idx)
    if not title:
        await call.answer("Некорректный выбор")
        return

    card_text = SERVICE_CARDS_BY_TITLE.get(title, f"{title}\n\nОписание скоро добавим.")
    await call.message.answer(card_text, reply_markup=service_card_kb(idx))
    await call.answer()


@router.callback_query(F.data.startswith("services:apply:"))
async def services_apply(call: CallbackQuery, state: FSMContext) -> None:
    raw = (call.data or "").split(":", 2)[2]
    try:
        idx = int(raw)
    except ValueError:
        await call.answer("Некорректный выбор")
        return

    title = _get_service_title(idx)
    if not title:
        await call.answer("Некорректный выбор")
        return

    await state.clear()
    await state.update_data(service=title, rest_type=None, files=[], contact=None)
    await call.answer()

    # Ветвления по услугам
    if _is_neuro_service(title):
        await state.set_state(LeadForm.neuro_step1)
        await call.message.answer(NEURO_STEP1_TEXT, reply_markup=neuro_step1_kb())
        if NEURO_EXAMPLE_PHOTO_FILE_IDS:
            media = [InputMediaPhoto(media=fid) for fid in NEURO_EXAMPLE_PHOTO_FILE_IDS[:5]]
            await call.message.answer_media_group(media=media)
        else:
            await call.message.answer("⚠️ Примеры фото пока не настроены (нет file_id).")
        return

    if _is_restoration_service(title):
        await state.set_state(LeadForm.rest_type)
        await call.message.answer("Что реставрируем?", reply_markup=restoration_type_kb())
        return

    if _is_model3d_service(title):
        await state.set_state(LeadForm.model3d_intro)
        await call.message.answer(MODEL3D_INTRO_TEXT, reply_markup=model3d_intro_kb())
        return

    if _is_content_service(title):
        await state.set_state(LeadForm.content_task)
        await call.message.answer(
            "📣 Контент для соцсетей / рекламы\n\n"
            "Кратко опишите задачу:\n"
            "— для какой платформы нужен контент\n"
            "  (Instagram, Telegram, реклама и т.д.)\n"
            "— для чего он нужен\n"
            "  (продажи, привлечение внимания, оформление профиля)\n"
            "— какой формат интересует\n"
            "  (картинки, короткие видео, серия постов, обложки)\n"
            "— есть ли примеры или стиль, который нравится\n"
            "  (можно ссылками)\n\n"
            "Если пока не уверены — опишите задачу в общих словах.\n"
            "Я задам уточняющие вопросы и предложу варианты."
        )
        return

    if _is_video_service(title):
        await state.set_state(LeadForm.video_task)
        await call.message.answer(
            "🎬 Видео-поздравление\n\n"
            "Представьте будущее видео и кратко опишите идею:\n\n"
            "— по какому поводу видео\n"
            "  (день рождения, Новый год, годовщина и т.д.)\n"
            "— для кого оно\n"
            "— какое настроение хочется передать\n"
            "  (трогательное, весёлое, торжественное)\n"
            "— есть ли пожелания по музыке или стилю\n\n"
            "Если пока нет чёткой идеи — напишите в общих словах.\n"
            "Я помогу сформировать концепцию и предложу варианты."
        )
        return

    # fallback: общий task
    await state.set_state(LeadForm.task)
    await call.message.answer("Опишите задачу одним сообщением (что нужно сделать):")


@router.callback_query(F.data.startswith("services:portfolio:"))
async def services_portfolio(call: CallbackQuery) -> None:
    raw = (call.data or "").split(":", 2)[2]
    try:
        idx = int(raw)
    except ValueError:
        await call.answer("Некорректный выбор")
        return

    title = _get_service_title(idx)
    if not title:
        await call.answer("Некорректный выбор")
        return

    file_ids = PORTFOLIO_MEDIA[idx - 1]
    if not is_configured(file_ids):
        await call.message.answer(
            f"Примеры для услуги «{title}» пока не настроены.\n"
            "Нужно добавить Telegram file_id изображений в bot/constants/portfolio.py",
            reply_markup=portfolio_after_album_kb(idx),
        )
        await call.answer()
        return

    media = [InputMediaPhoto(media=fid) for fid in file_ids[:5]]
    await call.message.answer_media_group(media=media)
    await call.message.answer("Хотите такой же результат?", reply_markup=portfolio_after_album_kb(idx))
    await call.answer()
