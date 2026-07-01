"""Project configuration loaded through PyCore ConfigManager."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pycore.core import BaseSettings, ConfigLoader, ConfigManager
from pydantic import Field, field_validator

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = PROJECT_ROOT / "backend"

DEFAULT_CORS_ORIGINS = [
    "http://localhost:5199",
    "http://127.0.0.1:5199",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
]
DEFAULT_BAILIAN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


class DotEnvConfigLoader(ConfigLoader):
    """Minimal .env loader registered through PyCore's config abstraction."""

    def supports(self, path: Path) -> bool:
        return path.name.startswith(".env")

    def load(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}

        config: dict[str, Any] = {}
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :].strip()
            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            config[key.strip().lower()] = _strip_quotes(value.strip())
        return config


class AppSettings(BaseSettings):
    """Runtime settings for the customer service bot API."""

    service_name: str = "customer-service-bot-api"
    environment: str = "local"
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 8099

    cors_origins: list[str] = Field(default_factory=lambda: list(DEFAULT_CORS_ORIGINS))
    cors_methods: list[str] = Field(default_factory=lambda: ["*"])
    cors_headers: list[str] = Field(default_factory=lambda: ["*"])

    database_path: str = "backend/data/customer_service.db"
    database_url: str = ""
    upload_dir: str = "backend/uploads"

    dashscope_api_key: str = Field(default="", repr=False)
    bailian_base_url: str = DEFAULT_BAILIAN_BASE_URL
    bailian_chat_model: str = "qwen-plus"
    bailian_embedding_model: str = "text-embedding-v4"
    bailian_embedding_dimensions: int = 1024
    sqlite_vector_extension_path: str = ""

    log_file_enabled: bool = False
    log_dir: str = "backend/logs"

    @field_validator("cors_origins", "cors_methods", "cors_headers", mode="before")
    @classmethod
    def _parse_list(cls, value: Any) -> Any:
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            if text.startswith("["):
                return json.loads(text)
            return [item.strip() for item in text.split(",") if item.strip()]
        return value

    def model_post_init(self, __context: Any) -> None:
        self.log_dir = str(_resolve_project_path(self.log_dir))
        self.upload_dir = str(_resolve_project_path(self.upload_dir))
        if self.database_url:
            self.database_url = _normalize_sqlite_url(self.database_url)
        else:
            database_path = _resolve_project_path(self.database_path)
            database_path.parent.mkdir(parents=True, exist_ok=True)
            self.database_url = f"sqlite+aiosqlite:///{database_path}"


_settings: AppSettings | None = None


def get_settings() -> AppSettings:
    """Return cached settings loaded from project .env files via ConfigManager."""

    global _settings
    if _settings is None:
        config_data = _load_dotenv_files()
        manager: ConfigManager[AppSettings] = ConfigManager.instance()
        manager.load_from_dict(AppSettings, config_data)
        _settings = manager.settings
    return _settings


def reset_settings_cache() -> None:
    """Reset settings cache for isolated tests."""

    global _settings
    _settings = None
    ConfigManager.reset()


def _load_dotenv_files() -> dict[str, Any]:
    loader = DotEnvConfigLoader()
    config: dict[str, Any] = {}
    for path in (
        PROJECT_ROOT / ".env",
        PROJECT_ROOT / ".env.local",
        BACKEND_ROOT / ".env",
        BACKEND_ROOT / ".env.local",
    ):
        config.update(loader.load(path))
    return config


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _resolve_project_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def _normalize_sqlite_url(url: str) -> str:
    for prefix in ("sqlite+aiosqlite:///", "sqlite:///"):
        if not url.startswith(prefix):
            continue

        raw_path = url[len(prefix) :]
        if raw_path in {"", ":memory:"}:
            return url

        database_path = Path(raw_path).expanduser()
        if not database_path.is_absolute():
            database_path = PROJECT_ROOT / database_path
        database_path.parent.mkdir(parents=True, exist_ok=True)
        return f"{prefix}{database_path.resolve()}"

    return url
