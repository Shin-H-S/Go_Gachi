# Supabase Auth Plan

로그인 기능은 `go-gachi-dev`에서 먼저 개발하고 검증합니다. 기능이 안정되면 같은 코드에 운영용 Supabase 환경변수를 주입해 `go-gachi-prod`로 배포합니다.

## Project Roles

- `go-gachi-dev`: 개발/테스트용 Supabase 프로젝트
- `go-gachi-prod`: 실제 사용자용 운영 Supabase 프로젝트

두 프로젝트는 사용자/관리자 서버를 나누는 목적이 아니라 환경을 분리하기 위한 것입니다. 사용자와 관리자는 같은 프로젝트 안에서 `profiles.role` 값으로 구분합니다.

```text
go-gachi-dev
- 로그인 개발
- 회원가입 테스트
- Google OAuth 테스트
- 권한 정책 검증

go-gachi-prod
- 실제 사용자 계정
- 운영 OAuth 설정
- 운영 DB/RLS 정책
- 운영 환경변수
```

## Auth Scope

1단계에서는 이메일/비밀번호 로그인을 기준으로 골격을 먼저 만듭니다. Google 로그인은 같은 Supabase Auth 흐름 위에 추가합니다.

구현 대상:

- Supabase 라이브러리 의존성 추가
- 환경변수 자리 마련
- 프론트 로그인/회원가입 화면
- 로그인 성공 시 토큰 저장
- 백엔드 요청에 `Authorization: Bearer` 자동 첨부
- 백엔드 JWT 검증 의존성
- 인증이 필요한 보호 라우트
- `profiles` 테이블과 `user`/`admin` 권한 구분

## Environment Variables

실제 키는 코드에 넣지 않고 환경변수로만 주입합니다.

```env
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_JWT_SECRET=
```

개발 중에는 `go-gachi-dev` 값을 사용하고, 운영 배포 시에는 `go-gachi-prod` 값을 사용합니다.

## Frontend Flow

프론트엔드는 Supabase Auth로 로그인하고, 성공한 세션의 access token을 보관합니다.

```text
1. 사용자가 이메일/비밀번호 또는 Google로 로그인
2. Supabase가 session/access token 발급
3. 프론트가 token을 session state에 저장
4. 백엔드 API 호출 시 Authorization 헤더 첨부
5. 로그아웃 시 session/token 제거
```

백엔드 호출 예시:

```http
Authorization: Bearer <supabase_access_token>
```

## Backend Flow

백엔드는 Supabase access token을 검증한 뒤, 필요한 API에서 로그인 여부와 role을 확인합니다.

```text
일반 보호 API
- 유효한 로그인 사용자면 접근 가능

관리자 API
- 유효한 로그인 사용자
- profiles.role == 'admin'
```

권장 라우트 구분:

```text
/api/auth/me
/api/protected/*
/api/admin/*
```

## Profiles Table

Supabase가 관리하는 `auth.users`와 별도로 앱 권한을 위한 `profiles` 테이블을 둡니다.

이 테이블은 **기존 테이블(`generations`, `api_usage`)과 동일하게 Alembic 마이그레이션으로 생성/관리**합니다. `auth.users`에 하드 외래키(FK)를 걸지 않고, `id`에는 Supabase 로그인 유저의 UUID(JWT의 `sub` 값)를 문자열로 저장합니다. 이렇게 하면 앱 DB 스키마 관리를 Alembic 한 곳으로 일관되게 유지할 수 있습니다. 운영/데모/배포 DB는 PostgreSQL(Supabase) 기준입니다.

```python
# backend/app/db/models.py (Alembic이 생성)
class Profile(Base):
    __tablename__ = "profiles"
    id: str            # Supabase 유저 UUID (JWT sub)
    email: str | None
    display_name: str | None
    role: str          # 'user' 또는 'admin' (기본 'user')
    created_at: datetime
    updated_at: datetime
```

프로필 행은 **첫 로그인 시 백엔드가 자동으로 upsert**합니다(없으면 `role='user'`로 생성). 관리자 권한은 DB를 따로 나누지 않고 `role` 값으로 부여하며, 승격은 다음 중 편한 방법으로 합니다.

- Supabase 대시보드(Table Editor)에서 해당 행의 `role`을 `admin`으로 수정
- 관리자 전용 엔드포인트(`PATCH /api/admin/users/{id}/role`)로 변경
- SQL 직접 실행

`role`은 우리 테이블 컬럼이라, 이후 `plan`, `is_blocked` 같은 권한/상태 컬럼도 자유롭게 확장할 수 있습니다.

## Branch Plan

현재 브랜치가 `refactor/db-improvements`라면 로그인 작업은 별도 브랜치에서 진행하는 것이 깔끔합니다.

권장 브랜치:

```text
feature/auth
```

## Implementation Order

1. `feature/auth` 브랜치 생성
2. Supabase 의존성 추가
3. 환경변수 샘플과 설정 로딩 추가
4. 프론트 로그인/회원가입 UI 추가
5. 프론트 세션 저장 및 API 인증 헤더 연결
6. 백엔드 JWT 검증 미들웨어/의존성 추가
7. `/api/auth/me` 또는 보호 라우트 추가
8. `profiles` 테이블 마이그레이션 추가
9. 관리자 전용 라우트와 role 검증 추가
10. `go-gachi-dev` 키로 로컬 검증
11. 운영 배포 시 `go-gachi-prod` 키로 환경변수 교체

## Start Checklist

시작 전에 확인할 항목:

- 골격부터 먼저 만들지 여부
- 브랜치 이름
- Supabase `go-gachi-dev`의 URL, anon key, JWT secret
- Google OAuth 설정을 1단계에 포함할지, 이메일/비밀번호 이후에 붙일지

권장 진행:

```text
1단계: 이메일/비밀번호 로그인 골격
2단계: 보호 라우트와 profiles.role 권한 검증
3단계: Google OAuth 추가
4단계: go-gachi-prod 운영 환경변수로 배포 검증
```
