from __future__ import annotations

# Один источник правды для идентификаторов услуг (нужно для callback_data и автозапуска сценариев).
# ВАЖНО: названия (title) должны совпадать с тем, что показывается в меню/каталоге.
SERVICE_ID_TO_TITLE: dict[str, str] = {
    "neuro": "🧠 Нейрофотосессия",
    "restoration": "🛠 Реставрация фото/видео",
    "model3d": "🎨 3D-модель по рисунку",
    "content": "📢 Контент для соцсетей/рекламы",
    "photo_stories": "🖼 Ролики и истории из фотографий",
    "video_greeting": "🎬 Видео-поздравление",
}

# Список услуг для UI (используется в заявке/услугах/примерах)
SERVICES: list[str] = list(SERVICE_ID_TO_TITLE.values())

# Обратный маппинг (если где-то приходит title)
SERVICE_TITLE_TO_ID: dict[str, str] = {v: k for k, v in SERVICE_ID_TO_TITLE.items()}


def get_service_title(service_id: str) -> str | None:
    return SERVICE_ID_TO_TITLE.get(service_id)


def get_service_id(service_title: str) -> str | None:
    return SERVICE_TITLE_TO_ID.get(service_title)
