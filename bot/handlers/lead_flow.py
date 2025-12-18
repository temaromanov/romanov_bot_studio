from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import ADMIN_TG_ID, DB_PATH
from bot.constants.services import SERVICES
from bot.db.repository import save_files, save_lead
from bot.keyboards.form import back_cancel_kb
from bot.keyboards.inline import (
    confirm_kb,
    deadline_kb,
    files_kb,
    restoration_type_kb,
    services_kb,
)
from bot.keyboards.main import main_menu_kb
from bot.services.leads import prepare_lead_data
from bot.states.lead_form import LeadForm
from bot.utils.validators import is_non_empty_text, validate_contact

router = Router()

MAX_FILES = 10

_DEADLINE_LABELS: dict[str, str] = {
    "urgent": "Срочно",
    "week": "В течение недели",
    "not_urgent": "Не срочно",
}


def _is_restoration_service(service: str) -> bool:
    s = (service or "").lower()
    return "реставрац" in s


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
    order = ["photo", "video", "doc"]
    labels = {"photo": "фото", "video": "видео", "doc": "док"}
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
    files_count = len(files)
    files_types = _file_kinds_human(files)
    files_block = ""
    if _is_restoration_service(service):
        files_block = f"\n<b>Файлы:</b> {files_count} (типы: {files_types})"

    return (
        "<b>Проверь заявку</b>\n\n"
        f"<b>Услуга:</b> {service}\n"
        f"<b>Задача:</b> {task}\n"
        f"<b>Срок:</b> {deadline}\n"
        f"<b>Контакт:</b> {contact}"
        f"{files_block}\n\n"
        "Если всё верно — жми «Отправить»."
    )


async def _ask_task(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    service = data.get("service") or ""
    prefix = f"Ок. Услуга: <b>{service}</b>\n\n" if service else ""
    await state.set_state(LeadForm.task)
    await message.answer(
        prefix + "Опишите задачу одним сообщением (что нужно сделать):",
        reply_markup=back_cancel_kb(),
    )


async def _ask_deadline(message: Message, state: FSMContext) -> None:
    await state.set_state(LeadForm.deadline)
    await message.answer("Выберите срочность:", reply_markup=deadline_kb())


async def _ask_contact(message: Message, state: FSMContext) -> None:
    await state.set_state(LeadForm.contact)
    await message.answer(
        "Оставьте контакт для связи (телефон / @username / ссылка):",
        reply_markup=back_cancel_kb(),
    )


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


@router.message(F.text == "✅ Оставить заявку")
async def start_lead_flow(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(LeadForm.choosing_service)
    await message.answer("Выберите услугу:", reply_markup=services_kb(SERVICES))


# ✅ старт заявки из inline-кнопок на статических страницах ("Как мы работаем" / "Контакты")
@router.callback_query(F.data == "lead:start")
async def start_lead_flow_from_inline(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
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

    await state.clear()
    await state.update_data(service=SERVICES[idx - 1], rest_type=None, files=[])

    service = SERVICES[idx - 1]
    await call.answer()

    if _is_restoration_service(service):
        await _ask_rest_type(call.message, state)
        return

    await _ask_task(call.message, state)


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
    await state.update_data(service=service, rest_type=None, files=[])

    await call.answer()

    if _is_restoration_service(service):
        await _ask_rest_type(call.message, state)
        return

    await _ask_task(call.message, state)


@router.message(F.text == "⬅️ Назад")
async def back_from_reply(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    data = await state.get_data()
    service = data.get("service") or ""

    if current == LeadForm.task.state:
        if _is_restoration_service(service):
            await _ask_rest_type(message, state)
            return
        await state.set_state(LeadForm.choosing_service)
        await message.answer("Выберите услугу:", reply_markup=services_kb(SERVICES))
        return

    if current == LeadForm.deadline_custom.state:
        await _ask_deadline(message, state)
        return

    if current == LeadForm.contact.state:
        await _ask_deadline(message, state)
        return

    await message.answer("Вы в меню.", reply_markup=main_menu_kb())


@router.callback_query(F.data == "lead:back")
async def back_from_inline(call: CallbackQuery, state: FSMContext) -> None:
    current = await state.get_state()

    if current == LeadForm.rest_type.state:
        await state.set_state(LeadForm.choosing_service)
        await call.message.answer("Выберите услугу:", reply_markup=services_kb(SERVICES))
        await call.answer()
        return

    if current == LeadForm.files.state:
        await call.answer()
        await _ask_task(call.message, state)
        return

    if current == LeadForm.deadline.state:
        await call.answer()
        await _ask_task(call.message, state)
        return

    if current == LeadForm.confirm.state:
        await call.answer()
        await _ask_contact(call.message, state)
        return

    await call.answer()


@router.callback_query(LeadForm.rest_type, F.data.in_({"rest:photo", "rest:video"}))
async def restoration_choose_type(call: CallbackQuery, state: FSMContext) -> None:
    rest_type = "Фото" if call.data == "rest:photo" else "Видео"
    await state.update_data(rest_type=rest_type)

    await call.answer()
    await _ask_task(call.message, state)


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


@router.message(LeadForm.contact)
async def input_contact(message: Message, state: FSMContext) -> None:
    contact = (message.text or "").strip()
    if not validate_contact(contact):
        await message.answer("Контакт слишком короткий. Напишите минимум 3 символа.", reply_markup=back_cancel_kb())
        return

    await state.update_data(contact=contact)
    await _show_confirm(message, state)


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
    contact = (data.get("contact") or "").strip()

    if not (service and task and deadline and contact):
        await call.answer("Данные заявки неполные. Начните заново.", show_alert=True)
        await _cancel_flow(call, state)
        return

    user = call.from_user

    files: list[dict[str, str]] = data.get("files") or []
    extra = {}
    if _is_restoration_service(service):
        extra = {
            "rest_type": data.get("rest_type"),
            "files_count": len(files),
            "files_types": _file_kinds_human(files),
        }

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

    if _is_restoration_service(service) and files:
        await save_files(DB_PATH, lead_id=lead_id, files=files)

    admin_text = (
        "🆕 Новая заявка\n"
        f"От: {(lead.get('tg_full_name') or 'Без имени')}"
        + (f" (@{lead.get('tg_username')})" if lead.get("tg_username") else "")
        + "\n"
        f"Услуга: {lead.get('service')}\n"
        f"Задача: {lead.get('task')}\n"
        f"Срок: {lead.get('deadline')}\n"
        f"Контакт: {lead.get('contact')}"
    )
    if _is_restoration_service(service):
        admin_text += f"\nФайлы: {len(files)} (типы: {_file_kinds_human(files)})"

    await call.bot.send_message(ADMIN_TG_ID, admin_text)

    await state.clear()
    await call.message.answer(
        f"✅ Заявка отправлена! Номер: <b>{lead_id}</b>\n"
        "Мы свяжемся с вами в ближайшее время.",
        reply_markup=main_menu_kb(),
    )
    await call.answer()
