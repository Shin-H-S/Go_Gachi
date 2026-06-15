# Deployment

현재 배포 기준은 백엔드 `Render`, 프론트엔드 `Streamlit Cloud`, 외부 스토리지 `Cloudflare R2`, DB `Supabase Postgres`입니다.

## Backend: Render

백엔드는 FastAPI 앱 `backend.app.main:app`을 실행합니다. Render 배포는 루트의 `render.yaml`과 `infra/Dockerfile`을 기준으로 합니다.

Render 컨테이너 시작 명령은 Dockerfile의 CMD를 사용합니다.

```bash
alembic upgrade head && uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

컨테이너 시작 시 Alembic 마이그레이션을 먼저 적용한 뒤 API 서버를 띄웁니다.

Render 필수 환경변수:

```env
APP_ENV=production
IMAGE_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_TEXT_MODEL=gpt-5.4-mini
OPENAI_IMAGE_MODEL=gpt-image-2
OPENAI_IMAGE_QUALITY=medium
DATABASE_URL=
CORS_ORIGINS=
STORAGE_BACKEND=r2
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_ENDPOINT_URL=
R2_BUCKET_NAME=
R2_PUBLIC_URL=
SUPABASE_URL=
SUPABASE_JWT_SECRET=
```

`CORS_ORIGINS`에는 Streamlit Cloud 프론트 주소를 넣습니다. 임시 검증 단계에서는 `*`를 쓸 수 있지만 운영에서는 프론트 URL로 제한합니다.

## Frontend: Streamlit Cloud

프론트엔드 엔트리포인트는 아래 파일입니다.

```text
frontend/app.py
```

Streamlit Cloud는 루트 `requirements.txt`를 프론트 배포 의존성 기준으로 사용합니다. 백엔드와 테스트 환경은 `pyproject.toml`과 `uv.lock`을 기준으로 관리합니다.

Streamlit Cloud 필수 환경변수:

```env
BACKEND_URL=https://YOUR_RENDER_BACKEND_URL
SUPABASE_URL=
SUPABASE_ANON_KEY=
FRONTEND_CONFIG_SOURCE=backend
```

`FRONTEND_CONFIG_SOURCE=backend`로 두면 배포 프론트가 백엔드 `/api/config`를 기준으로 프리셋을 읽습니다.

## Storage: Cloudflare R2

운영 생성 결과는 R2에 저장하고, 프론트에는 `imageUrl`을 우선 반환합니다.

- `STORAGE_BACKEND=r2`
- `R2_ENDPOINT_URL`: S3 호환 엔드포인트
- `R2_BUCKET_NAME`: 생성 결과와 업로드 원본을 저장할 버킷
- `R2_PUBLIC_URL`: 프론트에서 접근 가능한 공개 URL

로컬 검증에서는 `STORAGE_BACKEND=local`로 두고 `backend/uploads`, `backend/outputs` 폴더를 사용할 수 있습니다.

## Database: Supabase Postgres

운영 DB는 Supabase Postgres의 `DATABASE_URL`을 사용합니다. 앱 시작 시 테이블을 자동 생성하지 않고 Alembic 마이그레이션을 기준으로 관리합니다.

Supabase Auth 보호 API를 사용하려면 백엔드에 `SUPABASE_URL`과 `SUPABASE_JWT_SECRET`을 설정해야 합니다. 프론트에는 `SUPABASE_URL`과 `SUPABASE_ANON_KEY`를 설정합니다.

## Smoke Check

배포 후 백엔드에서 아래 엔드포인트를 확인합니다.

```text
GET /api/health
GET /api/ready
GET /api/config
```

`/api/ready` 응답의 `provider`가 `openai`인지 확인합니다.
