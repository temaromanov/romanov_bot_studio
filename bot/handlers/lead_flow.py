from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

from bot.config import ADMIN_TG_ID, DB_PATH
from bot.constants.services import SERVICES
from bot.db.repository import save_files, save_lead
from bot.keyboards.contact import contact_choice_kb, contact_input_kb
from bot.keyboards.form import back_cancel_kb
from bot.keyboards.inline import (
    confirm_kb,
    deadline_kb,
    files_kb,
    restoration_type_kb,
    services_kb,
)
from bot.keyboards.main import main_menu_kb
from bot.keyboards.model3d import model3d_intro_kb
from bot.keyboards.neuro import neuro_step1_kb, neuro_step2_kb
from bot.services.leads import prepare_lead_data
from bot.states.lead_form import LeadForm
from bot.texts.neuro import (
    NEURO_EXAMPLE_PHOTO_FILE_IDS,
    NEURO_STEP1_TEXT,
    NEURO_STEP2_TEXT,
    NEURO_WISHES_PROMPT,
)
from bot.texts.service_flows import CONTENT_TASK_TEXT, MODEL3D_INTRO_TEXT, VIDEO_TASK_TEXT
from bot.utils.replies import send_lead_success
from bot.utils.validators import is_non_empty_text, validate_contact

router = Router()

MAX_FILES = 10

_DEADLINE_LABELS: dict[str, str] = {
    "urgent": "Срочно",
    "week": "В течение недели",
    "not_urgent": "Не срочно",
}


def _is_restoration_service(service: str) -> bool:
    return "реставрац" in (service or "").lower()


def _is_neuro_service(service: str) -> bool:
    return "нейрофотосесс" in (service or "").lower()


def _is_content_service(service: str) -> bool:
    s = (service or "").lower()
    return "контент" in s and "соц" in s


def _is_video_service(service: str) -> bool:
    s = (service or "").lower()
    return "видео" in s and "поздрав" in s


def _is_model3d_service(service: str) -> bool:
    s = (service or "").lower()
    return "3d" in s and "модель" in s


def _file_kind_from_message(message: Message) -> tuple[str, str] | None:
    if message.photo:
        return ("photo", message.photo[-1].file_id)
    if message.video:
        return ("video", message.video.file_id)
    if message.document:
        return ("doc", message.document.file_id)
    return None


def _file_kinds_human(files: list[dict[str, str]]) -> str:
    kinds = {f.get("file_type") for f in files}
    order = ["photo", "video", "doc", "document_image"]
    labels = {"photo": "фото", "video": "видео", "doc": "док", "document_image": "док"}
    out = [labels[k] for k in order if k in kinds]
    return ", ".join(out) if out else "—"


async def _cancel_flow(target: Message | CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    text = "Ок, отменил. Возвращаю в меню 👇"
    if isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=main_menu_kb())
        await target.answer()
    else:
        await target.answer(text, reply_markup=main_menu_kb())


def _summary_text(data: dict) -> str:
    service = data.get("service") or "—"
    task = data.get("task") or "—"
    deadline = data.get("deadline") or "—"
    contact = data.get("contact") or "—"
    files: list[dict[str, str]] = data.get("files") or []

    lines = ["<b>Проверь заявку</b>", ""]
    lines.append(f"<b>Услуга:</b> {service}")

    if _is_neuro_service(service):
        lines.append(f"<b>Пожелания:</b> {task}")
    elif _is_model3d_service(service):
        lines.append(f"<b>Описание:</b> {task}")
    else:
        lines.append(f"<b>Задача:</b> {task}")

    lines.append(f"<b>Срок:</b> {deadline}")
    lines.append(f"<b>Контакт:</b> {contact}")

    if _is_restoration_service(service):
        lines.append(f"<b>Файлы:</b> {len(files)} (типы: {_file_kinds_human(files)})")
    if _is_model3d_service(service):
        lines.append(f"<b>Файлы:</b> {len(files)}")

    lines.append("")
    lines.append("Если всё верно — жми «Отправить».")
    return "\n".join(lines)


async def _ask_deadline(message: Message, state: FSMContext) -> None:
    await state.set_state(LeadForm.deadline)
    await message.answer("Выберите срочность:", reply_markup=deadline_kb())


async def _ask_contact(message: Message, state: FSMContext) -> None:
    await state.set_state(LeadForm.contact_choice)
    await message.answer("Как удобнее оставить контакт?", reply_markup=contact_choice_kb())


async def _show_confirm(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(LeadForm.confirm)
    await message.answer(_summary_text(data), reply_markup=confirm_kb())


async def _ask_rest_type(message: Message, state: FSMContext) -> None:
    await state.set_state(LeadForm.rest_type)
    await message.answer("Что реставрируем?", reply_markup=restoration_type_kb())


async def _ask_files(message: Message, state: FSMContext) -> None:
    await state.set_state(LeadForm.files)
    await message.answer(
        "Прикрепите файлы (фото/видео/документы).\n"
        f"Можно до {MAX_FILES} файлов. Когда закончите — нажмите «✅ Готово».",
        reply_markup=files_kb(),
    )


async def _ask_neuro_step1(message: Message, state: FSMContext) -> None:
    await state.set_state(LeadForm.neuro_step1)
    await message.answer(NEURO_STEP1_TEXT, reply_markup=neuro_step1_kb())

    if NEURO_EXAMPLE_PHOTO_FILE_IDS:
        media = [InputMediaPhoto(media=fid) for fid in NEURO_EXAMPLE_PHOTO_FILE_IDS[:5]]
        await message.answer_media_group(media=media)
    else:
        await message.answer("⚠️ Примеры фото пока не настроены (нет file_id).")


async def _ask_neuro_step2(message: Message, state: FSMContext) -> None:
    await state.set_state(LeadForm.neuro_step2)
    await message.answer(NEURO_STEP2_TEXT, reply_markup=neuro_step2_kb())


async def _ask_neuro_wishes(message: Message, state: FSMContext) -> None:
    await state.set_state(LeadForm.neuro_wishes)
    await message.answer(NEURO_WISHES_PROMPT, reply_markup=back_cancel_kb())


async def _ask_content_task(message: Message, state: FSMContext) -> None:
    await state.set_state(LeadForm.content_task)
    await message.answer(CONTENT_TASK_TEXT, reply_markup=back_cancel_kb())


async def _ask_video_task(message: Message, state: FSMContext) -> None:
    await state.set_state(LeadForm.video_task)
    await message.answer(VIDEO_TASK_TEXT, reply_markup=back_cancel_kb())


async def _ask_model3d_intro(message: Message, state: FSMContext) -> None:
    await state.set_state(LeadForm.model3d_intro)
    await message.answer(MODEL3D_INTRO_TEXT, reply_markup=model3d_intro_kb())


async def _ask_model3d_wait_file(message: Message, state: FSMContext) -> None:
    await state.set_state(LeadForm.model3d_wait_file)
    await message.answer(
        "Отправьте изображение (фото или документ с картинкой).\n"
        "Можно добавить текст в подписи (caption).",
        reply_markup=back_cancel_kb(),
    )


def _prev_task_route(service: str) -> str:
    if _is_neuro_service(service):
        return "neuro_wishes"
    if _is_restoration_service(service):
        return "task"
    if _is_model3d_service(service):
        return "model3d_wait_file"
    if _is_content_service(service):
        return "content_task"
    if _is_video_service(service):
        return "video_task"
    return "task"


@router.message(F.text == "✅ Оставить заявку")
async def start_lead_flow(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(LeadForm.choosing_service)
    await message.answer("Выберите услугу:", reply_markup=services_kb(SERVICES))


@router.callback_query(F.data == "lead:start")
async def start_lead_flow_from_inline(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(LeadForm.choosing_service)
    await call.message.answer("Выберите услугу:", reply_markup=services_kb(SERVICES))
    await call.answer()


@router.callback_query(F.data == "lead:back_to_services")
async def lead_back_to_services(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(LeadForm.choosing_service)
    await call.message.answer("Выберите услугу:", reply_markup=services_kb(SERVICES))
    await call.answer()


@router.callback_query(F.data.startswith("lead:svc:"))
async def start_lead_flow_with_service(call: CallbackQuery, state: FSMContext) -> None:
    raw = (call.data or "").split(":", 2)[2]
    try:
        idx = int(raw)
    except ValueError:
        await call.answer("Некорректный выбор")
        return

    if not (1 <= idx <= len(SERVICES)):
        await call.answer("Некорректный выбор")
        return

    service = SERVICES[idx - 1]
    await state.clear()
    await state.update_data(service=service, rest_type=None, files=[], contact=None)

    await call.answer()

    if _is_neuro_service(service):
        await _ask_neuro_step1(call.message, state)
        return
    if _is_restoration_service(service):
        await _ask_rest_type(call.message, state)
        return
    if _is_model3d_service(service):
        await _ask_model3d_intro(call.message, state)
        return
    if _is_content_service(service):
        await _ask_content_task(call.message, state)
        return
    if _is_video_service(service):
        await _ask_video_task(call.message, state)
        return

    await state.set_state(LeadForm.task)
    await call.message.answer("Опишите задачу одним сообщением (что нужно сделать):", reply_markup=back_cancel_kb())


@router.message(F.text == "❌ Отменить")
async def cancel_from_reply(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await message.answer("Вы в меню.", reply_markup=main_menu_kb())
        return
    await _cancel_flow(message, state)


@router.callback_query(F.data == "lead:cancel")
async def lead_cancel(call: CallbackQuery, state: FSMContext) -> None:
    await _cancel_flow(call, state)


@router.callback_query(LeadForm.choosing_service, F.data.startswith("svc:"))
async def choose_service(call: CallbackQuery, state: FSMContext) -> None:
    raw = (call.data or "").split(":", 1)[1]
    try:
        idx = int(raw)
    except ValueError:
        await call.answer("Некорректный выбор")
        return

    if not (1 <= idx <= len(SERVICES)):
        await call.answer("Некорректный выбор")
        return

    service = SERVICES[idx - 1]
    await state.update_data(service=service, rest_type=None, files=[], contact=None)

    await call.answer()

    if _is_neuro_service(service):
        await _ask_neuro_step1(call.message, state)
        return
    if _is_restoration_service(service):
        await _ask_rest_type(call.message, state)
        return
    if _is_model3d_service(service):
        await _ask_model3d_intro(call.message, state)
        return
    if _is_content_service(service):
        await _ask_content_task(call.message, state)
        return
    if _is_video_service(service):
        await _ask_video_task(call.message, state)
        return

    await state.set_state(LeadForm.task)
    await call.message.answer("Опишите задачу одним сообщением (что нужно сделать):", reply_markup=back_cancel_kb())


# ---------- Нейрофото ----------
@router.callback_query(LeadForm.neuro_step1, F.data == "neuro:step1_done")
async def neuro_step1_done(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await _ask_neuro_step2(call.message, state)


@router.callback_query(LeadForm.neuro_step2, F.data == "neuro:step2_done")
async def neuro_step2_done(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await _ask_neuro_wishes(call.message, state)


@router.callback_query(F.data == "neuro:back")
async def neuro_back(call: CallbackQuery, state: FSMContext) -> None:
    current = await state.get_state()
    if current == LeadForm.neuro_step2.state:
        await call.answer()
        await _ask_neuro_step1(call.message, state)
        return
    if current == LeadForm.neuro_step1.state:
        await state.set_state(LeadForm.choosing_service)
        await call.message.answer("Выберите услугу:", reply_markup=services_kb(SERVICES))
        await call.answer()
        return
    await call.answer()


@router.message(LeadForm.neuro_wishes)
async def neuro_wishes_input(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not is_non_empty_text(text):
        await message.answer("Напишите пожелания текстом (не пусто).", reply_markup=back_cancel_kb())
        return
    await state.update_data(task=text)
    await _ask_deadline(message, state)


# ---------- Контент ----------
@router.message(LeadForm.content_task)
async def content_task_input(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not is_non_empty_text(text):
        await message.answer("Напишите текстом (не пусто).", reply_markup=back_cancel_kb())
        return
    await state.update_data(task=text)
    await _ask_deadline(message, state)


# ---------- Видео ----------
@router.message(LeadForm.video_task)
async def video_task_input(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not is_non_empty_text(text):
        await message.answer("Напишите текстом (не пусто).", reply_markup=back_cancel_kb())
        return
    await state.update_data(task=text)
    await _ask_deadline(message, state)


# ---------- 3D ----------
@router.callback_query(LeadForm.model3d_intro, F.data == "model3d:next")
async def model3d_next(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await _ask_model3d_wait_file(call.message, state)


@router.message(LeadForm.model3d_wait_file)
async def model3d_wait_file(message: Message, state: FSMContext) -> None:
    files: list[dict[str, str]] = []

    if message.photo:
        fid = message.photo[-1].file_id
        files.append({"file_type": "photo", "file_id": fid})
    elif message.document:
        fid = message.document.file_id
        files.append({"file_type": "document_image", "file_id": fid})
    else:
        await message.answer("Нужно отправить изображение (фото или документ с картинкой).", reply_markup=back_cancel_kb())
        return

    caption = (message.caption or "").strip()
    await state.update_data(files=files, task=caption if caption else "—")
    await _ask_deadline(message, state)


# ---------- Реставрация ----------
@router.callback_query(LeadForm.rest_type, F.data.in_({"rest:photo", "rest:video"}))
async def restoration_choose_type(call: CallbackQuery, state: FSMContext) -> None:
    rest_type = "Фото" if call.data == "rest:photo" else "Видео"
    await state.update_data(rest_type=rest_type)
    await call.answer()
    await state.set_state(LeadForm.task)
    await call.message.answer("Опишите задачу одним сообщением (что нужно сделать):", reply_markup=back_cancel_kb())


@router.message(LeadForm.task)
async def input_task(message: Message, state: FSMContext) -> None:
    task_text = (message.text or "").strip()
    if not is_non_empty_text(task_text):
        await message.answer("Напишите задачу текстом (не пусто).", reply_markup=back_cancel_kb())
        return

    data = await state.get_data()
    service = data.get("service") or ""

    if _is_restoration_service(service):
        rest_type = (data.get("rest_type") or "").strip() or "—"
        task = f"Тип: {rest_type}\n{task_text}"
        await state.update_data(task=task)
        await _ask_files(message, state)
        return

    await state.update_data(task=task_text)
    await _ask_deadline(message, state)


@router.message(LeadForm.files, F.photo | F.video | F.document)
async def files_collect(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    files: list[dict[str, str]] = data.get("files") or []

    if len(files) >= MAX_FILES:
        await message.answer(
            f"Достигнут лимит {MAX_FILES} файлов.\n"
            "Нажмите «✅ Готово», чтобы продолжить.",
            reply_markup=files_kb(),
        )
        return

    parsed = _file_kind_from_message(message)
    if not parsed:
        await message.answer("Пришлите фото, видео или документ.", reply_markup=files_kb())
        return

    kind, file_id = parsed
    files.append({"file_type": kind, "file_id": file_id})
    await state.update_data(files=files)

    await message.answer(
        f"Принято: {kind}. Всего файлов: {len(files)}/{MAX_FILES}\n"
        "Можно прикрепить ещё или нажать «✅ Готово».",
        reply_markup=files_kb(),
    )


@router.callback_query(LeadForm.files, F.data == "files:done")
async def files_done(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    files: list[dict[str, str]] = data.get("files") or []

    if not files:
        await call.message.answer("⚠️ Файлы не прикреплены. Продолжаем без файлов.")
        await call.answer()
        await _ask_deadline(call.message, state)
        return

    await call.answer()
    await _ask_deadline(call.message, state)


@router.message(LeadForm.files)
async def files_unexpected_text(message: Message, state: FSMContext) -> None:
    await message.answer(
        "На этом шаге нужно прикрепить фото/видео/документы.\n"
        "Когда закончите — нажмите «✅ Готово».",
        reply_markup=files_kb(),
    )


# ---------- deadline ----------
@router.callback_query(LeadForm.deadline, F.data.startswith("dl:"))
async def choose_deadline(call: CallbackQuery, state: FSMContext) -> None:
    key = (call.data or "").split(":", 1)[1].strip()

    if key == "custom":
        await state.set_state(LeadForm.deadline_custom)
        await call.message.answer(
            "Напишите ваш вариант срока (например: «к пятнице», «до 10 января»):",
            reply_markup=back_cancel_kb(),
        )
        await call.answer()
        return

    if key not in _DEADLINE_LABELS:
        await call.answer("Некорректный выбор")
        return

    await state.update_data(deadline=_DEADLINE_LABELS[key])
    await call.answer()
    await _ask_contact(call.message, state)


@router.message(LeadForm.deadline_custom)
async def input_deadline_custom(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not is_non_empty_text(text):
        await message.answer("Напишите срок текстом (не пусто).", reply_markup=back_cancel_kb())
        return
    await state.update_data(deadline=text)
    await _ask_contact(message, state)


# ---------- contact (UX) ----------
@router.message(LeadForm.contact_choice, F.text == "✅ Использовать мой @username")
async def contact_use_username(message: Message, state: FSMContext) -> None:
    username = (message.from_user.username or "").strip()
    if not username:
        await message.answer(
            "У вас нет @username в Telegram.\nВыберите другой вариант (телефон или другой контакт).",
            reply_markup=contact_choice_kb(),
        )
        return
    await state.update_data(contact=f"@{username}")
    await _show_confirm(message, state)


@router.message(LeadForm.contact_choice, F.text == "📞 Указать телефон")
async def contact_phone_start(message: Message, state: FSMContext) -> None:
    await state.set_state(LeadForm.contact_phone)
    await message.answer("Введите номер телефона (минимум 6 символов):", reply_markup=contact_input_kb())


@router.message(LeadForm.contact_choice, F.text == "✍️ Ввести другой контакт")
async def contact_other_start(message: Message, state: FSMContext) -> None:
    await state.set_state(LeadForm.contact_other)
    await message.answer("Введите контакт (телефон / @username / ссылка):", reply_markup=contact_input_kb())


@router.message(LeadForm.contact_choice, F.text == "⏭ Пропустить")
async def contact_skip(message: Message, state: FSMContext) -> None:
    await state.update_data(contact="—")
    await _show_confirm(message, state)


@router.message(LeadForm.contact_phone)
async def contact_phone_input(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if len(text) < 6:
        await message.answer("Слишком коротко. Введите номер (минимум 6 символов):", reply_markup=contact_input_kb())
        return
    await state.update_data(contact=text)
    await _show_confirm(message, state)


@router.message(LeadForm.contact_other)
async def contact_other_input(message: Message, state: FSMContext) -> None:
    contact = (message.text or "").strip()
    if not validate_contact(contact):
        await message.answer("Контакт слишком короткий. Напишите минимум 3 символа.", reply_markup=contact_input_kb())
        return
    await state.update_data(contact=contact)
    await _show_confirm(message, state)


# ---------- Back (reply) ----------
@router.message(F.text == "⬅️ Назад")
async def back_from_reply(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    data = await state.get_data()
    service = data.get("service") or ""

    if current in {
        LeadForm.task.state,
        LeadForm.content_task.state,
        LeadForm.video_task.state,
        LeadForm.model3d_wait_file.state,
        LeadForm.neuro_wishes.state,
    }:
        if current == LeadForm.model3d_wait_file.state:
            await _ask_model3d_intro(message, state)
            return
        if current == LeadForm.neuro_wishes.state:
            await _ask_neuro_step2(message, state)
            return

        await state.set_state(LeadForm.choosing_service)
        await message.answer("Выберите услугу:", reply_markup=services_kb(SERVICES))
        return

    if current == LeadForm.deadline_custom.state:
        await _ask_deadline(message, state)
        return

    if current in {LeadForm.contact_choice.state, LeadForm.contact_phone.state, LeadForm.contact_other.state}:
        await _ask_deadline(message, state)
        return

    await message.answer("Вы в меню.", reply_markup=main_menu_kb())


# ---------- Back (inline) ----------
@router.callback_query(F.data == "lead:back")
async def back_from_inline(call: CallbackQuery, state: FSMContext) -> None:
    current = await state.get_state()
    data = await state.get_data()
    service = data.get("service") or ""

    if current == LeadForm.rest_type.state:
        await state.set_state(LeadForm.choosing_service)
        await call.message.answer("Выберите услугу:", reply_markup=services_kb(SERVICES))
        await call.answer()
        return

    if current == LeadForm.files.state:
        await call.answer()
        await state.set_state(LeadForm.task)
        await call.message.answer("Опишите задачу одним сообщением (что нужно сделать):", reply_markup=back_cancel_kb())
        return

    if current == LeadForm.deadline.state:
        await call.answer()
        prev = _prev_task_route(service)
        if prev == "neuro_wishes":
            await _ask_neuro_wishes(call.message, state)
            return
        if prev == "content_task":
            await _ask_content_task(call.message, state)
            return
        if prev == "video_task":
            await _ask_video_task(call.message, state)
            return
        if prev == "model3d_wait_file":
            await _ask_model3d_wait_file(call.message, state)
            return
        await state.set_state(LeadForm.task)
        await call.message.answer("Опишите задачу одним сообщением (что нужно сделать):", reply_markup=back_cancel_kb())
        return

    if current == LeadForm.confirm.state:
        await call.answer()
        await _ask_contact(call.message, state)
        return

    await call.answer()


# ---------- confirm/send ----------
@router.callback_query(LeadForm.confirm, F.data == "lead:edit")
async def lead_edit(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(LeadForm.choosing_service)
    await call.message.answer("Ок, давайте заново. Выберите услугу:", reply_markup=services_kb(SERVICES))
    await call.answer()


@router.callback_query(LeadForm.confirm, F.data == "lead:send")
async def lead_send(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()

    service = (data.get("service") or "").strip()
    task = (data.get("task") or "").strip()
    deadline = (data.get("deadline") or "").strip()
    contact = (data.get("contact") or "").strip() or "—"
    files: list[dict[str, str]] = data.get("files") or []

    if _is_model3d_service(service) and not files:
        await call.answer("Для 3D нужен файл (изображение).", show_alert=True)
        await _ask_model3d_wait_file(call.message, state)
        return

    if not (service and task and deadline):
        await call.answer("Данные заявки неполные. Начните заново.", show_alert=True)
        await _cancel_flow(call, state)
        return

    user = call.from_user

    extra = {}
    if _is_restoration_service(service):
        extra = {"rest_type": data.get("rest_type"), "files_count": len(files), "files_types": _file_kinds_human(files)}
    if _is_neuro_service(service):
        extra = {"wishes": task}

    lead = prepare_lead_data(
        tg_user_id=user.id,
        tg_username=user.username,
        tg_full_name=(user.full_name or "").strip() or "Пользователь",
        service=service,
        task=task,
        deadline_key="deadline:custom",
        deadline_custom_text=deadline,
        budget=None,
        contact=contact,
        extra=extra,
    )
    lead["deadline"] = deadline

    lead_id = await save_lead(
        DB_PATH,
        tg_user_id=lead["tg_user_id"],
        tg_username=lead["tg_username"],
        tg_full_name=lead["tg_full_name"],
        service=lead["service"],
        task=lead["task"],
        deadline=lead["deadline"],
        budget=lead["budget"],
        contact=lead["contact"],
        extra_json=lead["extra_json"],
    )

    if (_is_restoration_service(service) or _is_model3d_service(service)) and files:
        await save_files(DB_PATH, lead_id=lead_id, files=files)

    admin_text = (
        "🆕 Новая заявка\n"
        f"От: {(lead.get('tg_full_name') or 'Без имени')}"
        + (f" (@{lead.get('tg_username')})" if lead.get("tg_username") else "")
        + "\n"
        f"Услуга: {lead.get('service')}\n"
    )
    if _is_neuro_service(service):
        admin_text += f"Пожелания: {lead.get('task')}\n"
    elif _is_model3d_service(service):
        admin_text += f"Описание: {lead.get('task')}\n"
    else:
        admin_text += f"Задача: {lead.get('task')}\n"

    admin_text += f"Срок: {lead.get('deadline')}\nКонтакт: {lead.get('contact')}"

    if _is_restoration_service(service):
        admin_text += f"\nФайлы: {len(files)} (типы: {_file_kinds_human(files)})"
    if _is_model3d_service(service):
        admin_text += f"\nФайлы: {len(files)}"

    await call.bot.send_message(ADMIN_TG_ID, admin_text)

    await state.clear()
    await send_lead_success(call.message)
    await call.answer()
