# Go_Gachi

소상공인을 위한 광고 이미지 제작 서비스입니다.
사용자가 업로드한 메뉴/상품 이미지를 광고 채널 규격에 맞게 재구성하고, 광고 문구와 로고를 함께 반영해 홍보 이미지를 생성하는 MVP를 개발하고 있습니다.

## Current MVP

- Streamlit 프론트엔드에서 이미지 업로드, 채널/상세 규격 선택, 사용자 요청 입력을 받습니다.
- FastAPI 백엔드는 프리셋, 사용자 요청, 광고 문구, 로고 정보를 조합해 이미지 생성 프롬프트를 만듭니다.
- 광고 문구는 `gpt-5`로 생성하거나 다듬고, 최종 이미지는 `gpt-image-2`로 생성합니다.
- 문구는 별도 후처리 합성이 아니라 이미지 생성 프롬프트에 포함해 이미지 모델이 광고 이미지 안에 직접 렌더링하도록 합니다.
- 로고는 별도 픽셀 합성이 아니라 reference image로 이미지 모델에 전달합니다.
- 생성 결과는 선택한 상세 채널 규격의 PNG로 후처리하고, local 또는 Cloudflare R2 저장소에 저장할 수 있습니다.
- 생성 기록, 캐시, 사용량, 마이페이지 데이터는 PostgreSQL/Supabase 기준으로 관리합니다.

## Runtime

- Python `3.11.14`
- 패키지 관리: `uv`
- Backend: FastAPI
- Frontend: Streamlit
- DB: PostgreSQL / Supabase Postgres
- Storage: local 또는 Cloudflare R2
- Text model: `gpt-5`
- Image model: `gpt-image-2`

## Structure

```text
.github/        GitHub Actions, PR template
.vscode/        shared editor settings
backend/        FastAPI backend
config/         channel/detail presets
docs/           architecture, development, deployment docs
frontend/       Streamlit frontend
infra/          Docker runtime assets
migrations/     Alembic database migrations
scripts/        deploy/smoke helper scripts
tests/          backend/frontend automated tests
```

## Main Flow

1. 프론트가 `/api/config`로 사용 가능한 채널/상세 프리셋을 조회합니다.
2. 사용자가 메뉴 이미지, 광고 채널 상세 규격, 사용자 요청, 문구 사용 여부, 로고 이미지를 입력합니다.
3. 문구 사용이 켜져 있으면 백엔드가 `/api/copy/generate` 또는 생성 흐름 내부에서 광고 문구를 구성합니다.
4. 백엔드는 프리셋 프롬프트, 사용자 요청, 문구, 로고 위치를 이미지 생성 프롬프트로 조립합니다.
5. 백엔드는 메뉴 이미지와 로고 reference image를 OpenAI Images Edit API에 전달합니다.
6. 결과 이미지를 상세 규격 크기로 후처리하고 저장소에 저장합니다.
7. 프론트는 `imageDataUrl`로 미리보기하고, 필요하면 `imageUrl`로 저장된 이미지를 참조합니다.

## Main API

| Method | Path | Description |
| --- | --- | --- |
| GET | `/` | 서비스 기본 상태 |
| GET | `/api/health` | 외부 의존성 없는 헬스체크 |
| GET | `/api/ready` | 설정과 프리셋 로딩 상태 확인 |
| GET | `/api/config` | 프론트 초기 설정용 프리셋 목록 |
| POST | `/api/copy/generate` | 광고 문구 자동 생성 요청 |
| POST | `/api/generate` | 광고 이미지 생성 요청 |

상세 요청/응답 스키마는 [backend/README.md](backend/README.md)를 기준으로 확인합니다.

## Environment

레포 최상단 `.env`를 프론트/백엔드 공통 환경 파일로 사용합니다.
실제 API 키, DB URL, R2 키는 GitHub에 올리지 않습니다.

주요 환경변수:

```env
APP_ENV=production
IMAGE_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_TEXT_MODEL=gpt-5
OPENAI_IMAGE_MODEL=gpt-image-2
OPENAI_IMAGE_QUALITY=medium
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
STORAGE_BACKEND=local
CORS_ORIGINS=*
BACKEND_URL=http://127.0.0.1:8000
FRONTEND_USE_MOCK=false
FRONTEND_CONFIG_SOURCE=auto
```

R2를 사용할 때는 아래 값도 함께 설정합니다.

```env
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_ENDPOINT_URL=
R2_BUCKET_NAME=
R2_PUBLIC_URL=
```

전체 예시는 [.env.example](.env.example)를 참고합니다.

## Run

백엔드:

```bash
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

프론트엔드:

```bash
uv run streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501
```

공유 DB 또는 운영 DB를 처음 연결한 경우 마이그레이션을 먼저 적용합니다.

```bash
uv run alembic upgrade head
```

## Test

PR 전 기본 검증:

```bash
uv sync --all-groups
uv run ruff check .
uv run pytest -p no:cacheprovider
uv run python -m compileall backend frontend tests
```

## Deploy

이 저장소는 Cloud Run 배포를 고려해 구성되어 있습니다.
배포 환경에서는 `.env` 파일을 사용하지 않고, Secret Manager 또는 배포 플랫폼 Variables UI로 환경변수를 주입합니다.

GCP 배포 helper:

```powershell
.\scripts\gcp-deploy.ps1 -ProjectId YOUR_PROJECT_ID
```

배포 후 smoke test:

```powershell
.\scripts\gcp-smoke.ps1 -Url https://YOUR_SERVICE_URL
```

자세한 내용은 [docs/gcp.md](docs/gcp.md)를 참고합니다.

## Documentation

- [backend/README.md](backend/README.md): 백엔드 API, 문구/로고/스토리지 정책
- [frontend/README.md](frontend/README.md): 프론트 실행과 백엔드 연결 방식
- [docs/development.md](docs/development.md): 협업 개발 흐름
- [docs/database-migrations.md](docs/database-migrations.md): DB 마이그레이션 기준
- [docs/architecture.md](docs/architecture.md): 전체 구조와 런타임 흐름
- [docs/gcp.md](docs/gcp.md): GCP 배포 문서

## Notes

- 실제 시크릿은 절대 커밋하지 않습니다.
- `DATABASE_URL`은 PostgreSQL/Supabase 연결 문자열을 기준으로 합니다.
- SQLite는 격리 테스트에서 명시적으로 허용한 경우에만 사용합니다.
- production 환경에서는 내부 생성 프롬프트를 응답에 노출하지 않습니다.
- 로고는 reference image 기반 반영이므로, 완전한 원본 로고 합성이 필요하면 별도 후처리 설계를 검토해야 합니다.
