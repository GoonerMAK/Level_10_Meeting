from datetime import datetime

from app.core.config import settings


def utc_now() -> datetime:
    return settings.app_now
