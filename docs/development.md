# Development Workflow

이 프로젝트는 GCP/Cloud Run 배포를 우선 지원하도록 구성합니다. 다만 팀 개발, 테스트, 프론트 확인에는 같은 코드베이스를 로컬에서도 활용할 수 있습니다.

## Team Workflow

1. 브랜치 생성
2. 코드 수정
3. PR 생성
4. GitHub Actions CI 확인
5. 필요 시 Cloud Run 배포
6. 배포 URL 또는 로컬 검증 URL로 smoke test 실행

## CI Validation

프로젝트 Python 인터프리터는 `3.11.14`를 기준으로 맞춥니다.

PR과 `main` push에서 GitHub Actions가 아래 검증을 실행합니다.

```text
uv run ruff check .
uv run pytest
```

## Runtime Validation

Cloud Run 배포 후에는 서비스 URL에 대해 확인합니다.

```powershell
.\scripts\gcp-smoke.ps1 -Url https://YOUR_SERVICE_URL
```

확인 대상:

- `/api/health`
- `/api/ready`
- `/api/config`

## Database Migration

공유 개발 DB나 운영 DB는 PostgreSQL(Supabase) 기준입니다. 앱 시작 시 테이블을 자동 생성하지 않고, DB 스키마는 Alembic으로 관리합니다.

```powershell
uv run alembic upgrade head
```

`async_init_db()`는 pytest 격리 테스트용 보조 함수입니다. 팀 공용 DB나 배포 DB에는 위 마이그레이션 명령을 기준으로 맞춥니다.

## Environment

운영 런타임 환경변수는 Cloud Run에 주입합니다. `OPENAI_API_KEY`는 Secret Manager를 사용합니다.

```env
APP_ENV=production
IMAGE_PROVIDER=openai
OPENAI_TEXT_MODEL=gpt-5
OPENAI_IMAGE_MODEL=gpt-image-2
OPENAI_IMAGE_QUALITY=medium
```

로컬 `.env`는 레포 최상단 파일을 프론트/백엔드 공통 기준으로 사용합니다.
운영 값은 Cloud Run 환경변수와 Secret Manager에서 관리합니다.
