from datetime import UTC, datetime
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVER_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = SERVER_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(REPO_ROOT / ".env", SERVER_ROOT / ".env"), extra="ignore")

    database_url: str
    session_secret: SecretStr
    web_origin: str = "http://localhost:3000"
    seed_path: Path = REPO_ROOT / "assessment" / "seed.json"
    app_now: datetime = datetime(2026, 11, 11, 15, 0, tzinfo=UTC)


settings = Settings()
