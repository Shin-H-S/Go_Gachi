"""backend 폴더 기준 실행을 위한 호환용 진입점."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    # backend/main.py로 실행해도 루트 패키지 경로를 찾을 수 있게 보정한다.
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app  # noqa: E402,F401

__all__ = ["app"]
