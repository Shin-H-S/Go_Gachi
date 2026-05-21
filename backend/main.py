"""FastAPI 앱 시작점.

실행 (backend/ 폴더에서):
    uvicorn main:app --reload
확인:
    http://127.0.0.1:8000/health   →  {"status":"ok"}
    http://127.0.0.1:8000/docs     →  자동 API 문서 (여기서 /generate 테스트)
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.api.endpoints import router
from app.core import config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """앱 시작 시 업로드/결과 폴더와 DB 테이블을 준비한다.

    Args:
        app: FastAPI 앱 인스턴스.
    Returns:
        None (시작/종료 사이를 yield 로 구분).
    """
    config.ensure_dirs()
    try:
        from app.db.database import init_db

        init_db()
    except Exception as e:
        # DB가 아직 안 떠 있어도 서버는 켜지게 한다(/health 동작). /generate 시엔 실패.
        print(f"[경고] DB 초기화 실패 - 'docker compose up -d' 확인 필요: {e}")
    yield


app = FastAPI(title="AdMate AI Studio - 백엔드", lifespan=lifespan)

# 프론트엔드가 다른 포트에서 호출하므로 CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# 저장된 이미지를 URL로 열 수 있게 정적 파일 연결 (예: GET /uploads/xxx.png, /outputs/xxx.png)
config.ensure_dirs()  # mount 전에 폴더가 존재해야 함
app.mount("/uploads", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")
app.mount("/outputs", StaticFiles(directory=config.OUTPUT_DIR), name="outputs")
