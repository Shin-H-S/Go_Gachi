# 프론트엔드 로그인 연동 규격 (Auth Contract)

백엔드 로그인 기능이 준비됐습니다. 프론트는 아래 규격대로 연동하면 됩니다.
로그인 자체(비번 검증·토큰 발급·계정 생성)는 **Supabase**가 하고, 우리 백엔드는 **토큰 검증 + 권한 + 기록**만 합니다.

## 1. 전체 흐름

```
1. 프론트가 Supabase로 로그인  → access token(JWT) 받음
2. 토큰을 세션(st.session_state)에 저장
3. 백엔드 API 호출 시 헤더에  Authorization: Bearer <access_token>  첨부
4. 로그아웃 시 토큰 제거
```

## 2. 프론트에서 쓰는 Supabase 함수 (supabase-py)

```python
from supabase import create_client
client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# 회원가입 (이메일 인증 ON이라 session이 None일 수 있음 → "메일 확인" 안내)
res = client.auth.sign_up({"email": email, "password": password})

# 로그인 → res.session.access_token 가 백엔드에 보낼 토큰
res = client.auth.sign_in_with_password({"email": email, "password": password})
token = res.session.access_token
user_id = res.user.id
email = res.user.email

# 로그아웃
client.auth.sign_out()
```

- 비밀번호는 **최소 8자** (Supabase 설정). 프론트에서도 미리 검증 권장.
- **이메일 인증 ON**: 가입 직후엔 로그인 불가 → 가입 성공 시 "메일을 확인해 인증하세요" 안내 필요.
- access token은 **약 1시간 후 만료** → 길게 쓰면 `client.auth.refresh_session()`으로 갱신 필요.

## 3. 백엔드 API (프론트가 호출)

모든 보호 API는 헤더에 `Authorization: Bearer <access_token>` 필요.

### `GET /api/auth/me` — 내 정보 (로그인 확인용)
요청 헤더: `Authorization: Bearer <token>`
응답(200):
```json
{ "id": "uuid", "email": "a@b.com", "role": "user" }
```
- `role`은 `"user"` 또는 `"admin"`. (관리자 기능 노출 여부 판단에 사용)

### `GET /api/auth/me/generations` — 내 작업 기록
요청 헤더: `Authorization: Bearer <token>`
응답(200):
```json
{
  "items": [
    {
      "request_id": "uuid",
      "preset_id": "instagram",
      "status": "success",
      "image_url": null,
      "created_at": "2026-06-01T05:00:00"
    }
  ],
  "count": 1
}
```
- 최신순. 로그인한 본인 기록만 반환.

### `POST /api/generate` — 이미지 생성 (기존 + 토큰 선택)
- 요청 본문은 현재 생성 스키마를 사용합니다
  (`imageDataUrl`, `presetId`, `detailType`, `userPrompt`, `userCopy`, `copyMode`,
  `adCopyEnabled`, `targetWidth`, `targetHeight`).
- 헤더에 `Authorization: Bearer <token>`를 **넣으면** 생성 기록에 그 유저가 소유자로 저장됨(내 작업 기록에 잡힘).
- 토큰을 안 넣어도 생성은 됨(소유자만 비어있음).
- 응답 이미지는 `imageUrl`을 우선 사용합니다. `imageDataUrl`은 mock/fallback 응답에만
  있을 수 있으므로 프론트는 `imageUrl` 우선, `imageDataUrl` fallback으로 처리합니다.

호출 예시:
```python
import httpx
headers = {"Authorization": f"Bearer {token}"} if token else None
r = httpx.post(f"{BACKEND_URL}/api/generate", json=payload, headers=headers, timeout=90)
```

## 4. 에러 코드 의미

| 코드 | 의미 | 프론트 처리 |
|---|---|---|
| 401 | 토큰 없음/만료/위조 | 로그인 화면으로 보냄(또는 토큰 갱신) |
| 403 | 로그인은 됐지만 권한 부족(관리자 전용) | "권한 없음" 표시 |
| 503 | 백엔드에 인증 미설정(SUPABASE_JWT_SECRET 없음) | 보통 개발 중에만, 환경변수 확인 |

## 5. 환경변수 (프론트)

```env
SUPABASE_URL=<go-gachi-dev 프로젝트 URL>
SUPABASE_ANON_KEY=<go-gachi-dev anon public key>
```

- 개발은 `go-gachi-dev` 값, 운영 배포 시 `go-gachi-prod` 값으로 교체.
- `anon key`는 공개돼도 되는 키(프론트용). `JWT secret`은 백엔드 전용이라 프론트에 절대 넣지 않음.

## 6. role 값

- `"user"`: 일반 사용자(기본값)
- `"admin"`: 관리자. 관리자 전용 화면/버튼은 `/api/auth/me`의 `role == "admin"`일 때만 노출.
- 관리자 승격은 Supabase 대시보드/관리 API로 `profiles.role`을 바꿔서 부여.
