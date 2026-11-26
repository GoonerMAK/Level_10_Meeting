from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

SERVER_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = SERVER_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(REPO_ROOT / ".env", SERVER_ROOT / ".env"), extra="ignore")

    database_url: str
    seed_path: Path = REPO_ROOT / "assessment" / "seed.json"


settings = Settings()
