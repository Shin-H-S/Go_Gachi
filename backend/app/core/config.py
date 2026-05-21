"""앱 전역 설정.

backend/.env 파일의 값을 읽어 하나의 `settings` 객체로 만든다.
코드 전체에서 `from app.core.config import settings` 로 가져다 쓴다.
비밀값(OPENAI_API_KEY 등)은 .env 에만 두고 코드/깃에는 박지 않는다.
"""

import json
from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ 폴더 경로 (이 파일 기준 2단계 위: core -> app -> backend)
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    """환경설정 묶음. 각 항목은 .env 의 같은 이름 값으로 덮어쓸 수 있다.

    아래 기본값은 .env 에 해당 키가 없을 때 쓰이는 값이다.
    """

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
    def split_cors(cls, value: str | list[str]) -> list[str]:
        # .env에서 JSON 배열 또는 콤마 문자열 둘 다 편하게 쓸 수 있도록 허용합니다.
        if isinstance(value, str):
            if value.strip().startswith("["):
                return json.loads(value)
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("UPLOAD_DIR", "OUTPUT_DIR", mode="after")
    @classmethod
    def resolve_path(cls, value: Path) -> Path:
        # 상대 경로로 입력되면 backend 폴더 기준 경로로 변환합니다.
        return value if value.is_absolute() else BASE_DIR / value

    @property
    def max_bytes(self) -> int:
        """업로드 최대 용량을 MB 설정값에서 바이트 단위로 환산해 돌려준다."""
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @property
    def openai_enabled(self) -> bool:
        """OpenAI 키가 채워져 있으면 True (키 값 자체는 노출하지 않음)."""
        return bool(self.OPENAI_API_KEY)

    def ensure_dirs(self) -> None:
        """업로드/결과 저장 폴더가 없으면 만든다(서버 시작 시 호출)."""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
