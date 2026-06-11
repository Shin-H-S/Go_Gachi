# Architecture

## Runtime Flow

1. 사용자는 Streamlit 프론트엔드(`frontend/app.py`)에 접속합니다.
2. 사용자가 카페 메뉴 사진을 업로드하고 광고 채널과 추가 요청 문구를 입력합니다.
3. 프론트엔드는 업로드 이미지를 base64 data URL로 변환하고, 선택된 preset id, detail type, feedback, 상세 출력 크기(`targetWidth`, `targetHeight`)를 `/api/generate`로 보냅니다.
4. FastAPI 백엔드는 `/api/config`에서 제공하는 프리셋과 상세 유형 기준으로 요청을 검증합니다.
5. FastAPI는 서버 환경변수에서만 OpenAI API 키를 읽고, 이미지 검증·캐시 조회·OpenAI 이미지 편집 호출을 처리합니다.
   OpenAI 호출 직전에는 업로드 이미지를 EXIF 보정 후 PNG/RGB로 정규화해 특이한 이미지 모드로 인한 API 거절을 줄입니다.
6. 백엔드는 생성 결과를 선택 상세 크기의 PNG로 후처리해 `imageDataUrl`로 반환하고, 프론트엔드는 결과 미리보기와 다운로드를 제공합니다. 최종 후처리는 기본 `cover`이며, API에서 `resizeMode=contain`을 보내면 원본 전체를 보존하고 남는 영역을 흐림 배경으로 채웁니다.

프론트엔드는 기본적으로 `BACKEND_URL=http://127.0.0.1:8000`을 사용해 같은 서버의
FastAPI를 호출합니다. 백엔드 연결 실패 시에는 목업으로 대체하지 않고 에러를 표시합니다.
화면 확인용 목업은 `FRONTEND_USE_MOCK=true`를 명시한 경우에만 사용합니다.
프론트 프리셋은 `FRONTEND_CONFIG_SOURCE=auto` 기준으로 백엔드 `/api/config`를 먼저
읽고, 백엔드가 준비되지 않은 경우 로컬 `config/presets.json`으로 fallback합니다.

채널별·상세 유형별 전용 프롬프트는 `config/presets.json`에서 관리하고, 백엔드의 `backend/app/core/prompts.py`에서 최종 프롬프트로 조립합니다.

업로드 허용 형식은 JPG, PNG, WEBP입니다. 원본은 저장/캐시 키 기준으로 유지하고,
OpenAI에 전송하는 파일만 PNG/RGB로 정규화합니다. 입력 이미지 진단 로그에는 포맷,
모드, 크기처럼 디버깅에 필요한 메타데이터만 기록합니다.

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
