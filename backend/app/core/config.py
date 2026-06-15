"""런타임 설정과 환경변수 로딩."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parents[3]
CONFIG_DIR = ROOT_DIR / "config"
ALLOW_SQLITE_DATABASE_ENV = "ALLOW_SQLITE_DATABASE"


def _parse_csv(value: str, *, default: list[str]) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or default


def _load_env_file(env_path: Path) -> None:
    """단일 .env 파일을 현재 프로세스 환경변수로 적재한다."""
    if not env_path.exists():
        return

    import os

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

        # 이미 주입된 환경변수(운영 환경)가 루트 .env보다 우선이므로 덮어쓰지 않는다.
        if key in os.environ:
            continue

        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]

        os.environ[key] = value


def load_env() -> None:
    """공통 .env를 환경변수로 적재한다.

    운영에서는 Render/Streamlit Cloud 같은 호스팅 플랫폼의 환경변수를 사용한다.
    로컬 검증에서는 레포 최상단 `.env`만 프론트/백엔드 공통 기준으로 읽는다.
    """
    _load_env_file(ROOT_DIR / ".env")


DEFAULT_DATA_DIR = ROOT_DIR / "backend" / "data"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "backend" / "outputs"
DEFAULT_UPLOAD_DIR = ROOT_DIR / "backend" / "uploads"


class Settings(BaseModel):
    """앱 전체에서 참조하는 런타임 설정값."""

    app_env: str = "local"
    port: int = 8000
    image_provider: Literal["mock", "openai"] = "mock"
    openai_api_key: str = ""
    openai_admin_key: str = ""
    openai_text_model: str = "gpt-5.4-mini"
    openai_image_model: str = "gpt-image-2"
    openai_image_quality: str = "medium"
    max_upload_bytes: int = 50 * 1024 * 1024

    # DB 라우팅용 설정. 실제 실행/데모/배포는 PostgreSQL DATABASE_URL을 필수로 받는다.
    database_url: str = ""
    # data/output/upload 경로는 보통 기본값으로 충분하지만, 테스트·Docker·운영 컨테이너에서 임시
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

    # 외부 스토리지(Cloudflare R2). STORAGE_BACKEND=r2일 때만 사용.
    # local이면 disk(uploads/outputs)를, r2면 R2 버킷에 객체로 저장한다.
    storage_backend: Literal["local", "r2"] = "local"
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_endpoint_url: str = ""
    r2_bucket_name: str = ""
    r2_public_url: str = ""
    cors_origins: list[str] = ["*"]


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
    database_url = _database_url_from_env()

    return Settings(
        port=int(os.getenv("PORT", "8000")),
        app_env=os.getenv("APP_ENV", "local"),
        image_provider=provider,
        openai_api_key=api_key,
        openai_admin_key=os.getenv("OPENAI_ADMIN_KEY", ""),
        openai_text_model=os.getenv("OPENAI_TEXT_MODEL", "gpt-5.4-mini"),
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
        storage_backend=os.getenv("STORAGE_BACKEND", "local"),
        r2_access_key_id=os.getenv("R2_ACCESS_KEY_ID", ""),
        r2_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY", ""),
        r2_endpoint_url=os.getenv("R2_ENDPOINT_URL", ""),
        r2_bucket_name=os.getenv("R2_BUCKET_NAME", ""),
        r2_public_url=os.getenv("R2_PUBLIC_URL", ""),
        cors_origins=_parse_csv(os.getenv("CORS_ORIGINS", "*"), default=["*"]),
    )


def _database_url_from_env() -> str:
    """DATABASE_URL을 검증해서 반환한다.

    실제 실행/데모/배포는 PostgreSQL을 기준으로 한다. SQLite는 pytest 격리 테스트처럼
    명시적으로 허용한 경우에만 사용할 수 있다.
    """
    import os

    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required. Set a PostgreSQL/Supabase connection string.")

    if database_url.startswith("sqlite"):
        allow_sqlite = os.getenv(ALLOW_SQLITE_DATABASE_ENV, "").strip().lower()
        if allow_sqlite not in {"1", "true", "yes"}:
            raise RuntimeError(
                "SQLite DATABASE_URL is only allowed for isolated tests. "
                f"Use PostgreSQL for runtime or set {ALLOW_SQLITE_DATABASE_ENV}=true in tests."
            )

    return database_url
