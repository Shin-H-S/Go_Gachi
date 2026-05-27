# Development Workflow

이 프로젝트는 로컬 앱 실행을 지원하지 않고, GCP/Cloud Run 서버 실행을 기준으로 개발합니다.

## Team Workflow

1. 브랜치 생성
2. 코드 수정
3. PR 생성
4. GitHub Actions CI 확인
5. Cloud Run 배포
6. 배포 URL로 smoke test 실행

## CI Validation

프로젝트 Python 인터프리터는 `3.11.14`를 기준으로 맞춥니다.

PR과 `main` push에서 GitHub Actions가 아래 검증을 실행합니다.

```text
uv run ruff check .
uv run pytest
```

## GCP Runtime Validation

배포 후 Cloud Run URL에 대해 확인합니다.

```powershell
.\scripts\gcp-smoke.ps1 -Url https://YOUR_SERVICE_URL
```

확인 대상:

- `/api/health`
- `/api/ready`
- `/api/config`

## Environment

런타임 환경변수는 Cloud Run에 주입합니다. `OPENAI_API_KEY`는 Secret Manager를 사용합니다.

```env
APP_ENV=production
IMAGE_PROVIDER=openai
OPENAI_TEXT_MODEL=gpt-5
OPENAI_IMAGE_MODEL=gpt-image-2
OPENAI_IMAGE_QUALITY=medium
```

로컬 `.env`는 서버 실행 용도로 사용하지 않습니다.
