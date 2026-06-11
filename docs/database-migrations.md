# Database Migrations

DB 스키마는 Alembic 마이그레이션으로 관리합니다. FastAPI 앱은 시작 시 운영 테이블을 자동 생성하지 않습니다.

## 원칙

- 운영/데모/배포 DB는 PostgreSQL(Supabase) 기준입니다.
- `DATABASE_URL`은 PostgreSQL 연결 문자열로 설정합니다.
- `DATABASE_URL`이 가리키는 DB에만 마이그레이션이 적용됩니다.
- 개발자용 DB와 사용자/운영 DB는 분리합니다.
- 실제 `.env`, DB 비밀번호, Supabase 연결 문자열은 GitHub에 올리지 않습니다.
- `async_init_db()`는 pytest 격리 테스트용 보조 함수입니다. 실제 실행용 DB 초기화에는 사용하지 않습니다.

## 자주 쓰는 명령

```powershell
uv run alembic upgrade head
uv run alembic current
uv run alembic check
```

모델 변경 후 새 마이그레이션을 만들 때:

```powershell
uv run alembic revision --autogenerate -m "describe change"
```

## 새 PostgreSQL DB 연결 순서

1. 새 DB를 만든다.
2. `.env` 또는 런타임 환경변수에 `DATABASE_URL`을 설정한다.
3. `uv run alembic upgrade head`를 실행한다.
4. 백엔드를 실행하거나 배포한다.

## 관련 파일

- `alembic.ini`: Alembic 기본 설정
- `migrations/env.py`: 앱 설정 기반 DB 연결과 마이그레이션 실행 로직
- `migrations/versions/`: 버전별 마이그레이션 스크립트
- `backend/app/db/models.py`: ORM 모델
- `backend/app/db/database.py`: DB 엔진과 세션 유틸리티
