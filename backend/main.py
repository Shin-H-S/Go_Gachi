"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.endpoints import router
from app.core.config import settings


def create_app() -> FastAPI:
    # 서버 시작 시 업로드/결과 폴더를 보장해 파일 저장 단계에서 실패하지 않게 합니다.
    settings.ensure_directories()

    app = FastAPI(title=settings.PROJECT_NAME)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # 모든 API는 /api/v1 아래에 모아 프론트엔드가 버전 단위로 붙을 수 있게 합니다.
    app.include_router(router, prefix=settings.API_PREFIX)
    # 생성된 결과 이미지는 프론트가 바로 미리보기 할 수 있도록 정적 경로로 제공합니다.
    app.mount("/outputs", StaticFiles(directory=settings.OUTPUT_DIR), name="outputs")

    return app


app = create_app()
