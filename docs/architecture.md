# Architecture

## Runtime Flow

1. 사용자는 Streamlit 프론트엔드(`frontend/app.py`)에 접속합니다.
2. 프론트는 `/api/config`를 호출해 채널/상세 광고 규격 프리셋을 가져옵니다.
3. 사용자는 메뉴 사진, 광고 채널 상세 규격, 이미지 방향 요청, 광고 문구 사용 여부, 로고 이미지를 입력합니다.
4. 프론트는 업로드 이미지를 base64 data URL로 변환하고, `presetId`, `detailType`, `userPrompt`, `copyMode`, `adCopyEnabled`, `userCopy`, `logoDataUrl`, `targetWidth`, `targetHeight`를 `/api/generate`로 보냅니다.
5. 광고 문구 자동 생성 버튼을 누르는 경우 프론트는 `/api/copy/generate`로 먼저 문구를 요청합니다.
6. FastAPI 백엔드는 프리셋과 상세 유형 기준으로 요청을 검증합니다.
7. `adCopyEnabled=true`이면 백엔드는 OpenAI Responses API와 `gpt-5`로 광고 문구를 생성하거나 정리합니다.
8. 백엔드는 프리셋 프롬프트, 사용자 요청, 문구 결과, 로고 위치 지시를 이미지 생성 프롬프트로 조립합니다.
9. OpenAI 호출 직전 업로드 이미지를 EXIF 보정 후 PNG/RGB로 정규화합니다. 로고가 있으면 로고도 reference image로 정규화합니다.
10. 백엔드는 OpenAI Images Edit API와 `gpt-image-2`로 광고 이미지를 생성합니다.
11. 생성 결과를 선택 상세 크기의 PNG로 후처리합니다. 기본은 `cover`이고, `resizeMode=contain`이면 원본 전체를 보존하고 남는 영역을 흐림 배경으로 채웁니다.
12. 결과는 local 또는 R2 저장소에 저장하고, DB에는 생성 기록, 캐시 키, 사용량, 저장 path/key를 남깁니다.
13. 프론트는 응답의 `imageDataUrl`로 미리보기와 다운로드를 제공하고, `copy`, `logo`, `imageUrl`을 결과 요약에 활용합니다.

## Frontend Runtime

프론트엔드는 기본적으로 `BACKEND_URL=http://127.0.0.1:8000`을 사용해 같은 서버의 FastAPI를 호출합니다.
백엔드 연결 실패 시에는 목업으로 대체하지 않고 에러를 표시합니다.
화면 확인용 목업은 `FRONTEND_USE_MOCK=true`를 명시한 경우에만 사용합니다.

프론트 프리셋은 `FRONTEND_CONFIG_SOURCE=auto` 기준으로 백엔드 `/api/config`를 먼저 읽고, 백엔드가 준비되지 않은 경우 로컬 `config/presets.json`으로 fallback합니다.

## Backend Runtime

- `backend/app/main.py`: FastAPI 앱, 라우트, 미들웨어 등록
- `backend/app/schemas.py`: 요청/응답 스키마
- `backend/app/core/prompts.py`: 프리셋/사용자 요청/문구/로고 지시를 이미지 프롬프트로 조립
- `backend/app/services/openai_copy.py`: 문구 모델 호출
- `backend/app/services/openai_images.py`: 이미지 모델 호출
- `backend/app/services/generation_service.py`: 검증, 캐시, 저장, OpenAI 호출을 묶는 생성 흐름
- `backend/app/services/storage/`: local/R2 저장소 구현

## Prompt Source

채널별·상세 유형별 전용 프롬프트는 `config/presets.json`에서 관리합니다.
백엔드는 `prompt_hint`, `channel_prompt`, 상세 유형 프롬프트, 사용자 요청, 광고 문구, 로고 위치를 조합해 OpenAI Images API에 전달합니다.

## Upload And Storage

- 업로드 허용 형식은 JPG, PNG, WEBP입니다.
- 원본은 저장/캐시 키 기준으로 유지합니다.
- OpenAI에 전송하는 파일만 PNG/RGB로 정규화합니다.
- 입력 이미지 진단 로그에는 포맷, 모드, 크기처럼 디버깅에 필요한 메타데이터만 기록합니다.
- `STORAGE_BACKEND=local`이면 `backend/uploads`, `backend/outputs`를 사용합니다.
- `STORAGE_BACKEND=r2`이면 Cloudflare R2 버킷에 객체로 저장합니다.

## Cloud Runtime

Cloud Run runs the same FastAPI app from the Docker image built by `infra/Dockerfile`.
The container listens on the `PORT` environment variable provided by Cloud Run.
Secrets are injected at runtime through Secret Manager, not copied into the image.

## Folder Layout

- `backend/app`: FastAPI application code
- `config`: product presets and editable non-secret configuration
- `frontend`: Streamlit frontend application and related assets
- `infra`: Docker runtime assets
- `migrations`: Alembic database migrations
- `docs`: project documentation
- `tests`: automated tests
- `.github`: pull request and CI configuration
- `.vscode`: shared VSCode recommendations
- `cloudbuild.yaml`: Cloud Build pipeline for Cloud Run

## Secret Handling

Never place real API keys in source files.
Local development uses `.env`, which is ignored by git and Docker build context.
Cloud Run should use Secret Manager and inject `OPENAI_API_KEY`, `DATABASE_URL`, Supabase secrets, and R2 secrets as environment variables at runtime.
