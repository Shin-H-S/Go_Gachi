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


DEFAULT_DATA_DIR = ROOT_DIR / "backend" / "data"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "backend" / "outputs"
DEFAULT_UPLOAD_DIR = ROOT_DIR / "backend" / "uploads"


class Settings(BaseModel):
    """앱 전체에서 참조하는 런타임 설정값."""

    app_env: str = "local"
    port: int = 8080
    image_provider: Literal["mock", "openai"] = "mock"
    openai_api_key: str = ""
    openai_admin_key: str = ""
    openai_text_model: str = "gpt-5"
    openai_image_model: str = "gpt-image-2"
    openai_image_quality: str = "medium"
    max_upload_bytes: int = 50 * 1024 * 1024

    # DB 라우팅용 설정. 운영 이전 시 DATABASE_URL 한 줄만 교체하면 PostgreSQL로 간다.
    database_url: str = f"sqlite:///{(DEFAULT_DATA_DIR / 'app.db').as_posix()}"
    # data/output/upload 경로는 보통 기본값으로 충분하지만, 테스트·Docker·Cloud Run에서 임시
    # 폴더로 리다이렉트할 수 있게 env override를 남겨둔다.
    data_dir: Path = DEFAULT_DATA_DIR
    output_dir: Path = DEFAULT_OUTPUT_DIR
    upload_dir: Path = DEFAULT_UPLOAD_DIR

    # 비용 추적: gpt-image류 1콜 ≈ $0.01. 데모 기간 안전 한도 $30, 경고 $25.
    openai_image_edit_estimated_cost_usd: float = 0.01
    openai_budget_limit_usd: float = 30.0
    openai_budget_alert_usd: float = 25.0

    # 인증(Supabase Auth)용 설정. 비어 있으면 백엔드 인증 검증을 끈다(현 단계 호환).
    # - supabase_url / supabase_anon_key: 프론트가 로그인할 때 사용(참고용으로 백엔드도 보관).
    # - supabase_jwt_secret: 백엔드가 프론트에서 받은 JWT를 검증할 때 쓰는 비밀키.
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_jwt_secret: str = ""


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

    data_dir = Path(os.getenv("DATA_DIR", str(DEFAULT_DATA_DIR)))
    output_dir = Path(os.getenv("OUTPUT_DIR", str(DEFAULT_OUTPUT_DIR)))
    upload_dir = Path(os.getenv("UPLOAD_DIR", str(DEFAULT_UPLOAD_DIR)))
    # DB URL 기본값은 data_dir/app.db. 환경변수로 명시하면 Supabase/PostgreSQL로 그대로 전환.
    database_url = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(data_dir / 'app.db').as_posix()}",
    )

    return Settings(
        port=int(os.getenv("PORT", "8080")),
        app_env=os.getenv("APP_ENV", "local"),
        image_provider=provider,
        openai_api_key=api_key,
        openai_admin_key=os.getenv("OPENAI_ADMIN_KEY", ""),
        openai_text_model=os.getenv("OPENAI_TEXT_MODEL", "gpt-5"),
        openai_image_model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2"),
        openai_image_quality=os.getenv("OPENAI_IMAGE_QUALITY", "medium"),
        database_url=database_url,
        data_dir=data_dir,
        output_dir=output_dir,
        upload_dir=upload_dir,
        openai_image_edit_estimated_cost_usd=float(
            os.getenv("OPENAI_IMAGE_EDIT_ESTIMATED_COST_USD", "0.01")
        ),
        openai_budget_limit_usd=float(os.getenv("OPENAI_BUDGET_LIMIT_USD", "30.0")),
        openai_budget_alert_usd=float(os.getenv("OPENAI_BUDGET_ALERT_USD", "25.0")),
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
        supabase_jwt_secret=os.getenv("SUPABASE_JWT_SECRET", ""),
    )
