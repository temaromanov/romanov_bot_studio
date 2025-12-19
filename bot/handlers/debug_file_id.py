from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

router = Router()


@router.message(F.photo)
async def debug_photo_file_id(message: Message) -> None:
    file_id = message.photo[-1].file_id
    await message.answer(f"📸 PHOTO file_id:\n<code>{file_id}</code>")


@router.message(F.video)
async def debug_video_file_id(message: Message) -> None:
    file_id = message.video.file_id
    await message.answer(f"🎬 VIDEO file_id:\n<code>{file_id}</code>")


@router.message(F.document)
async def debug_document_file_id(message: Message) -> None:
    file_id = message.document.file_id
    mime = message.document.mime_type
    await message.answer(
        f"📎 DOCUMENT file_id:\n<code>{file_id}</code>\n"
        f"mime: <code>{mime}</code>"
    )
