"""pytest 공통 설정.

`backend.app.*` 모듈이 import 되기 전에 환경변수를 덮어써서, 테스트가 실제
프로젝트의 SQLite 파일이나 outputs 폴더를 건드리지 않게 한다.

  - DATABASE_URL → 임시 폴더의 SQLite 파일
  - DATA_DIR / OUTPUT_DIR → 임시 폴더
  - APP_ENV=test
  - IMAGE_PROVIDER=mock (특정 테스트는 monkeypatch로 openai로 바꿔 사용)
  - OPENAI_API_KEY 비움(실제 키가 .env에 있어도 테스트에 새지 않게)
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

_TEST_DIR = Path(tempfile.mkdtemp(prefix="go-gachi-tests-"))
_TEST_DIR.mkdir(parents=True, exist_ok=True)
(_TEST_DIR / "outputs").mkdir(parents=True, exist_ok=True)
(_TEST_DIR / "uploads").mkdir(parents=True, exist_ok=True)

# 테스트는 항상 임시 DB/폴더만 사용한다. 기존 환경변수에 실제 DB가 있어도 덮어쓴다.
os.environ["PYTHON_DOTENV_DISABLED"] = "1"
os.environ["DATABASE_URL"] = f"sqlite:///{(_TEST_DIR / 'app.db').as_posix()}"
os.environ["ALLOW_SQLITE_DATABASE"] = "true"
os.environ["DATA_DIR"] = str(_TEST_DIR)
os.environ["OUTPUT_DIR"] = str(_TEST_DIR / "outputs")
os.environ["UPLOAD_DIR"] = str(_TEST_DIR / "uploads")
os.environ["APP_ENV"] = "test"
os.environ["IMAGE_PROVIDER"] = "mock"
os.environ["FRONTEND_CONFIG_SOURCE"] = "local"
# 외부 R2를 건드리지 않도록 테스트는 항상 local 디스크 모드로 시작한다.
# r2 모드를 검증하는 테스트는 monkeypatch로 settings.storage_backend를 바꾼다.
os.environ["STORAGE_BACKEND"] = "local"
# 실 API 키가 흘러들어가 실제 호출이 발생하지 않도록 항상 비운다.
os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_ADMIN_KEY"] = ""

# 테스트 시작 시점에 기존 캐시된 settings를 무효화(타 테스트가 먼저 import 했을 가능성).
from backend.app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()


@pytest.fixture()
def anyio_backend() -> str:
    """anyio 기반 async 테스트는 asyncio 백엔드만 사용한다."""
    return "asyncio"


def pytest_sessionfinish(session, exitstatus) -> None:  # noqa: ARG001
    """모든 테스트가 끝나면 임시 폴더 정리."""
    shutil.rmtree(_TEST_DIR, ignore_errors=True)
