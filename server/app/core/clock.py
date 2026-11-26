import time
from datetime import datetime, timedelta

from app.core.config import settings

STARTED_AT = time.monotonic()


def utc_now() -> datetime:
    return settings.app_now + timedelta(seconds=time.monotonic() - STARTED_AT)
