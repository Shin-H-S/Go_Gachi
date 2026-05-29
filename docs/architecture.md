# Architecture

## Runtime Flow

1. 사용자는 Streamlit 프론트엔드(`frontend/app.py`)에 접속합니다.
2. 사용자가 카페 메뉴 사진을 업로드하고 광고 채널과 추가 요청 문구를 입력합니다.
3. 프론트엔드는 업로드 이미지를 base64 data URL로 변환하고, 선택된 preset id와 feedback을 `/api/generate`로 보냅니다.
4. FastAPI 백엔드는 `/api/config`에서 제공하는 프리셋 기준으로 요청을 검증합니다.
5. FastAPI는 서버 환경변수에서만 OpenAI API 키를 읽고, 이미지 검증·캐시 조회·OpenAI 이미지 편집 호출을 처리합니다.
6. 백엔드는 생성 결과를 `imageDataUrl`로 반환하고, 프론트엔드는 결과 미리보기와 다운로드를 제공합니다.

`BACKEND_URL`이 없는 프론트 실행 환경에서는 화면 확인용 mock 이미지를 생성합니다. 실제 백엔드 연동 시에는 `BACKEND_URL`로 FastAPI 서버 URL을 주입합니다.

## Cloud Runtime

Cloud Run runs the same FastAPI app from the Docker image built by `infra/Dockerfile`. The container listens on the `PORT` environment variable provided by Cloud Run. Secrets are injected at runtime through Secret Manager, not copied into the image.

## Folder Layout

- `backend/app`: FastAPI application code
- `config`: product presets and editable non-secret configuration
- `frontend`: Streamlit frontend application and related assets
- `infra`: Docker runtime assets
- `docs`: project documentation
- `tests`: automated tests
- `.github`: pull request and CI configuration
- `.vscode`: shared VSCode recommendations
- `cloudbuild.yaml`: Cloud Build pipeline for Cloud Run

## Secret Handling

Never place real API keys in source files. Local development uses `.env`, which is ignored by git and Docker build context. Cloud Run should use Secret Manager and inject `OPENAI_API_KEY` as an environment variable at runtime.
