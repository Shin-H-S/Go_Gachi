"""앱 환경설정 (간단 버전).

베이스라인에선 외부 의존성 없이 경로/CORS만 둔다.
.env 로딩·OpenAI 키·DB 접속정보는 다음 단계에서 추가한다.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# backend/ 폴더 (이 파일 기준 3단계 위: core -> app -> backend)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# backend/.env 에서 환경변수 로드 (비밀값은 .env 에만, 코드엔 안 박는다)
load_dotenv(BASE_DIR / ".env")

UPLOAD_DIR = BASE_DIR / "uploads"  # 업로드된 원본 사진
OUTPUT_DIR = BASE_DIR / "outputs"  # 생성된 결과 이미지

# 프론트엔드 주소(CORS). 아직 미정이라 우선 전체 허용으로 시작.
CORS_ORIGINS = ["*"]

# OpenAI 키 (나중에 사용). 지금은 더미라 없어도 됨.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# --- MySQL 접속 정보 (.env 에서 로드, docker-compose 와 공유) ---
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3307")  # movie_mysql(3306) 충돌 피해 3307 사용
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")  # 비밀번호는 .env 에서만 (코드/깃 노출 금지)
DB_NAME = os.getenv("DB_NAME", "go_gachi")
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"


def ensure_dirs() -> None:
    """업로드/결과 폴더가 없으면 생성한다.

    Args:
        없음.
    Returns:
        None.
    """
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
