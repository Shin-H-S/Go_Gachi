"""Application settings loaded from backend/.env."""

import json
from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    # API와 모델, 저장소 설정은 .env에서 덮어쓸 수 있게 한 곳에 모읍니다.
    PROJECT_NAME: str = "Go Gachi Ads"
    ENVIRONMENT: str = "local"
    API_PREFIX: str = "/api/v1"

    OPENAI_API_KEY: str = ""
    OPENAI_IMAGE_MODEL: str = "gpt-image-1-mini"
    OPENAI_TEXT_MODEL: str = "gpt-4.1-mini"

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    MAX_UPLOAD_MB: int = 12
    ALLOWED_IMAGE_CONTENT_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]

    LANGSMITH_TRACING: Optional[bool] = False
    LANGSMITH_API_KEY: Optional[str] = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors_origins(cls, value: str | list[str]) -> list[str]:
        # .env에서 JSON 배열 또는 콤마 문자열 둘 다 편하게 쓸 수 있도록 허용합니다.
        if isinstance(value, str):
            if value.strip().startswith("["):
                return json.loads(value)
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("UPLOAD_DIR", "OUTPUT_DIR", mode="after")
    @classmethod
    def resolve_storage_path(cls, value: Path) -> Path:
        # 상대 경로로 입력되면 backend 폴더 기준 경로로 변환합니다.
        return value if value.is_absolute() else BASE_DIR / value

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @property
    def openai_enabled(self) -> bool:
        return bool(self.OPENAI_API_KEY)

    def ensure_directories(self) -> None:
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
