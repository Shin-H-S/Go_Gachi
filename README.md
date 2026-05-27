# Go_Gachi

소상공인을 위한 광고 이미지 제작 서비스입니다. 이 저장소는 **GCP/Cloud Run 실행 기준**으로 관리합니다. 앱 서버를 로컬에서 실행하지 않고, 배포된 GCP 서버에서 동작을 확인합니다.

## Structure

```text
.github/        # CI, PR template
.vscode/        # shared editor settings
backend/        # FastAPI backend
config/         # image preset config
docs/           # architecture and GCP operation docs
frontend/       # Streamlit frontend starter structure
infra/          # Cloud Run Dockerfile
scripts/        # GCP deploy/smoke scripts
tests/          # backend tests used by CI
```

## Runtime

Python interpreter:

```text
Python 3.11.14
```

Cloud Run runtime entrypoint:

```text
uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8080}
```

Runtime environment is injected by Cloud Run / Cloud Build, not by a local `.env`.

Required runtime variables:

```env
APP_ENV=production
IMAGE_PROVIDER=openai
OPENAI_API_KEY=<Secret Manager>
OPENAI_TEXT_MODEL=gpt-5
OPENAI_IMAGE_MODEL=gpt-image-2
OPENAI_IMAGE_QUALITY=medium
```

## API

- `GET /`
- `GET /api/health`
- `GET /api/ready`
- `GET /api/config`
- `POST /api/generate`

`POST /api/generate` receives a base64 image data URL, preset id, and feedback. It returns the edited image as a data URL.

## GCP Deploy

```powershell
.\scripts\gcp-deploy.ps1 -ProjectId YOUR_PROJECT_ID
```

After deployment:

```powershell
.\scripts\gcp-smoke.ps1 -Url https://YOUR_SERVICE_URL
```

More details: [docs/gcp.md](docs/gcp.md)

## CI

CI runs on GitHub Actions:

```text
uv run ruff check .
uv run pytest
```
