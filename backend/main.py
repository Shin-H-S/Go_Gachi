"""FastAPI 앱 시작점.

uvicorn 이 여기서 만든 `app` 객체를 불러 서버를 띄운다.
실행 (backend/ 폴더에서):
    uvicorn main:app --reload
"""

from app.api.endpoints import router
from app.core.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


def create_app() -> FastAPI:
    """FastAPI 앱을 만들어 설정을 끼운 뒤 돌려준다(app factory 패턴).

    여기서 한 곳에 모아 설정하므로, 테스트할 때 새 앱을 따로 만들기도 쉽다.

    Returns:
        FastAPI: 폴더 준비 + CORS + 라우터(/api/v1) + 정적경로(/outputs)까지
            모두 설정된 앱 인스턴스.
    """
    # 서버 시작 시 업로드/결과 폴더를 보장해 파일 저장 단계에서 실패하지 않게 합니다.
    settings.ensure_dirs()

    app = FastAPI(title=settings.PROJECT_NAME)
    # CORS: 프론트엔드가 다른 주소(포트)에서 호출해도 브라우저가 막지 않게 허용한다.
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
