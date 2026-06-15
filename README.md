# Go_Gachi

소상공인을 위한 광고 이미지 제작 서비스입니다. 현재 배포 기준은 백엔드 `Render`, 프론트엔드 `Streamlit Cloud`, 외부 스토리지 `Cloudflare R2`, DB `Supabase Postgres`입니다.

## Structure

```text
.github/        # CI, PR template
.vscode/        # shared editor settings
backend/        # FastAPI backend
config/         # image preset config
docs/           # architecture, development, deployment docs
frontend/       # Streamlit frontend
infra/          # Render backend Dockerfile
render.yaml     # Render backend blueprint
scripts/        # manual utility scripts
tests/          # backend tests used by CI
```

## Runtime

Python interpreter:

```text
Python 3.11.14
```

Backend runtime entrypoint:

```text
uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

운영 런타임 환경변수는 Render와 Streamlit Cloud의 환경변수 UI에서 주입합니다. 로컬 검증 시에는 레포 최상단 `.env`를 프론트/백엔드 공통 기준으로 사용합니다.

Required runtime variables:

```env
APP_ENV=production
IMAGE_PROVIDER=openai
OPENAI_API_KEY=<Render secret>
OPENAI_TEXT_MODEL=gpt-5.4-mini
OPENAI_IMAGE_MODEL=gpt-image-2
OPENAI_IMAGE_QUALITY=medium
DATABASE_URL=<Supabase Postgres URL>
STORAGE_BACKEND=r2
R2_ENDPOINT_URL=<Cloudflare R2 endpoint>
R2_BUCKET_NAME=<Cloudflare R2 bucket>
R2_PUBLIC_URL=<Cloudflare R2 public URL>
```

## API

- `GET /`
- `GET /api/health`
- `GET /api/ready`
- `GET /api/config`
- `POST /api/generate`

`POST /api/generate` receives a base64 input image data URL, preset id, detail type,
image prompt, and optional ad copy. It stores the generated PNG and returns `imageUrl`
first; `imageDataUrl` is kept only for mock/fallback responses.

## Deploy

배포 절차와 환경변수는 [docs/deployment.md](docs/deployment.md)를 기준으로 관리합니다.

## CI

CI runs on GitHub Actions:

```text
uv run ruff check .
uv run pytest
```
