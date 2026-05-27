"""Cloud Run 런타임 설정과 환경변수 로딩."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parents[3]
CONFIG_DIR = ROOT_DIR / "config"


def load_env() -> None:
    """필요 시 루트 .env를 환경변수로 적재한다.

    운영에서는 Cloud Run 환경변수를 사용하지만, 테스트나 임시 검증에서는 같은 설정 객체를
    재사용할 수 있게 둔다.
    """
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        # 빈 줄, 주석, KEY=VALUE 형식이 아닌 줄은 무시한다.
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        import os

        # 이미 주입된 환경변수는 Cloud Run 설정이 우선이므로 덮어쓰지 않는다.
        if key in os.environ:
            continue

        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]

        os.environ[key] = value


class Settings(BaseModel):
    """앱 전체에서 참조하는 런타임 설정값."""

    app_env: str = "local"
    port: int = 8080
    image_provider: Literal["mock", "openai"] = "mock"
    openai_api_key: str = ""
    openai_text_model: str = "gpt-5"
    openai_image_model: str = "gpt-image-2"
    openai_image_quality: str = "medium"
    max_upload_bytes: int = 50 * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """환경변수를 Settings 객체로 변환한다.

    lru_cache로 요청마다 환경변수를 다시 읽지 않게 한다.
    """
    load_env()

    import os

    api_key = os.getenv("OPENAI_API_KEY", "")
    # provider를 명시하지 않아도 키가 있으면 openai, 없으면 mock으로 동작한다.
    provider = os.getenv("IMAGE_PROVIDER") or ("openai" if api_key else "mock")

    return Settings(
        port=int(os.getenv("PORT", "8080")),
        app_env=os.getenv("APP_ENV", "local"),
        image_provider=provider,
        openai_api_key=api_key,
        openai_text_model=os.getenv("OPENAI_TEXT_MODEL", "gpt-5"),
        openai_image_model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2"),
        openai_image_quality=os.getenv("OPENAI_IMAGE_QUALITY", "medium"),
    )
