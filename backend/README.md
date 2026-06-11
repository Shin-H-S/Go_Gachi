# Go_Gachi Backend

소상공인 광고 이미지 제작 서비스의 FastAPI 백엔드입니다.
현재 MVP는 사용자가 업로드한 메뉴/상품 이미지, 채널 프리셋, 사용자 요청, 광고 문구, 로고 이미지를 받아 광고용 이미지로 재구성합니다.

## Runtime

- Python `3.11.14`
- 패키지 관리: `uv`
- 기본 실행 앱: `backend.app.main:app`
- 이미지 모델: `gpt-image-2`
- 문구 모델: `gpt-5`

Railway, Cloud Run 같은 컨테이너 기반 운영 환경을 지원하며, 같은 앱을 로컬 검증 환경에서도 실행할 수 있게 구성합니다.

## MVP Flow

1. 프론트가 `/api/config`로 사용 가능한 채널/상세 프리셋을 가져옵니다.
2. 사용자가 메뉴 이미지, 채널 상세 규격, 사용자 요청, 광고 문구 사용 여부, 로고 이미지를 선택합니다.
3. `adCopyEnabled=true`이면 백엔드가 문구 모델로 광고 문구를 생성하거나 정리합니다.
4. 백엔드는 프리셋 프롬프트, 사용자 요청, 광고 문구, 로고 위치 지시를 하나의 이미지 생성 프롬프트로 조립합니다.
5. 메뉴 이미지와 선택 로고 이미지를 OpenAI Images Edit API에 전달합니다.
6. 결과 이미지를 선택한 상세 규격 크기로 후처리하고 local 또는 R2 저장소에 저장합니다.
7. 응답에는 미리보기용 `imageDataUrl`, 저장소 접근용 `imageUrl`, 문구 결과, 로고 반영 정보를 함께 내려줍니다.

## Main API

| Method | Path | Description |
| --- | --- | --- |
| GET | `/` | 서비스 기본 상태 |
| GET | `/api/health` | 외부 의존성 없는 헬스체크 |
| GET | `/api/ready` | 설정과 프리셋 로딩 상태 확인 |
| GET | `/api/config` | 프론트 초기 설정용 프리셋 목록 |
| POST | `/api/copy/generate` | 광고 문구 자동 생성 요청 |
| POST | `/api/generate` | 광고 이미지 생성 요청 |

`APP_ENV=production`이 아니면 내부 점검용 `/api/internal/*` 라우터도 함께 등록됩니다.

## Config Response

프론트는 `/api/config` 응답으로 채널/상세 규격과 업로드 제한을 구성합니다.

```json
{
  "presets": [],
  "provider": "openai",
  "maxUploadBytes": 52428800
}
```

- `presets`: `config/presets.json`에서 로드한 채널/상세 광고 규격 목록입니다.
- `provider`: 현재 이미지 생성 provider입니다. `mock` 또는 `openai`입니다.
- `maxUploadBytes`: 백엔드가 허용하는 단일 이미지 data URL 최대 크기입니다.

## Copy Generate Request

`/api/copy/generate`는 이미지 생성 전에 광고 문구만 먼저 만들거나 다듬을 때 사용합니다.

```json
{
  "presetId": "instagram",
  "detailType": "story_image",
  "userPrompt": "아메리카노 할인 행사를 강조하고 싶어요.",
  "copyMode": "rewrite"
}
```

| Field | Description |
| --- | --- |
| `presetId` | `GET /api/config`에서 받은 채널 프리셋 ID입니다. 생략하면 기본 프리셋을 사용합니다. |
| `detailType` | 프리셋 안의 상세 광고 유형 ID입니다. 생략하면 해당 프리셋의 기본 상세 유형을 사용합니다. |
| `userPrompt` | 문구 생성에 참고할 사용자 요청입니다. |
| `copyMode` | `preserve`, `polish`, `rewrite` 중 하나입니다. 기본값은 `rewrite`입니다. |

응답은 아래 형식입니다.

```json
{
  "headline": "오늘 아메리카노 2,500원",
  "subcopy": "카페에서 더 맛있게 즐겨보세요.",
  "cta": null,
  "copyMode": "rewrite"
}
```

## Generate Request

`/api/generate`는 최종 광고 이미지를 생성합니다. 현재 스키마는 JSON 요청만 사용합니다.

```json
{
  "imageDataUrl": "data:image/png;base64,...",
  "presetId": "instagram",
  "detailType": "story_image",
  "userPrompt": "창가 감성의 따뜻한 카페 광고 이미지로 만들어줘",
  "copyMode": "polish",
  "adCopyEnabled": true,
  "userCopy": "오늘 아메리카노 2,500원",
  "logoDataUrl": "data:image/png;base64,...",
  "logoPosition": "bottom_right",
  "parentRequestId": null,
  "targetWidth": 1080,
  "targetHeight": 1920,
  "resizeMode": "cover"
}
```

| Field | Description |
| --- | --- |
| `imageDataUrl` | 필수. JPG, PNG, WEBP data URL입니다. |
| `presetId` | 채널 프리셋 ID입니다. 생략하면 기본 프리셋을 사용합니다. |
| `detailType` | 상세 광고 유형 ID입니다. 생략하면 프리셋 기본 상세 유형을 사용합니다. |
| `userPrompt` | 이미지 방향성에 대한 사용자 요청입니다. |
| `copyMode` | 문구 처리 방식입니다. `preserve`, `polish`, `rewrite`를 지원합니다. |
| `adCopyEnabled` | 광고 문구를 최종 이미지에 포함할지 여부입니다. |
| `userCopy` | 사용자가 입력한 광고 문구입니다. 최대 300자입니다. |
| `logoDataUrl` | 선택. 로고 반영에 사용할 JPG, PNG, WEBP data URL입니다. |
| `logoPosition` | 로고 위치 지시입니다. `top_left`, `top_right`, `bottom_left`, `bottom_right`, `center_bottom`을 지원합니다. |
| `parentRequestId` | 수정 이력 연결용 부모 생성 ID입니다. 현재는 스키마만 열어둔 상태입니다. |
| `targetWidth`, `targetHeight` | 최종 출력 픽셀 크기입니다. 둘 중 하나만 보낼 수 없습니다. |
| `resizeMode` | 최종 후처리 방식입니다. `cover` 또는 `contain`을 지원하며 기본값은 `cover`입니다. |

알 수 없는 `presetId` 또는 `detailType`은 프론트 연동 오류를 빨리 찾을 수 있도록 `400`으로 응답합니다.

## Generate Response

```json
{
  "imageDataUrl": "data:image/png;base64,...",
  "imageUrl": "https://cdn.example.com/outputs/20260611-abcd.png",
  "provider": "openai",
  "preset": {
    "id": "instagram",
    "label": "인스타그램"
  },
  "copy": {
    "headline": "오늘 아메리카노 2,500원",
    "subcopy": "카페에서 더 맛있게 즐겨보세요.",
    "cta": null,
    "copyMode": "polish"
  },
  "logo": {
    "used": true,
    "position": "bottom_right"
  },
  "revision": null,
  "note": null,
  "prompt": null
}
```

- `imageDataUrl`: 프론트가 바로 미리보기할 수 있는 PNG data URL입니다.
- `imageUrl`: 저장소에 저장된 결과 이미지 접근 URL입니다. mock 분기에서는 `null`일 수 있습니다.
- `provider`: 실제 처리에 사용된 provider입니다.
- `preset`: 요청에 사용된 프리셋 정보입니다.
- `copy`: `adCopyEnabled=true`일 때 내려가는 문구 처리 결과입니다.
- `logo`: `logoDataUrl`이 있을 때 내려가는 로고 반영 정보입니다.
- `revision`: 수정 이력용 응답 영역입니다. 현재는 후속 구현을 위해 열어둔 필드입니다.
- `note`: mock 또는 캐시 사용 같은 부가 안내입니다.
- `prompt`: `APP_ENV=production`에서는 내부 프롬프트 보호를 위해 `null`입니다. local/dev에서는 디버깅용으로 포함될 수 있습니다.

## Error Response

현재 브랜치의 주요 수동 검증 오류는 FastAPI 기본 형식인 `detail`로 내려갑니다.

```json
{
  "detail": "지원하지 않는 presetId입니다: unknown"
}
```

이미지 생성 중 외부 API나 서버 의존성 문제가 발생하면 사용자에게 일반화된 `503` 메시지를 내려주고, 실제 원인은 서버 로그에 남깁니다.

## Copy Policy

- 문구 생성은 `backend/app/services/openai_copy.py`에서 OpenAI Responses API를 사용합니다.
- `IMAGE_PROVIDER=mock`이거나 `OPENAI_API_KEY`가 없으면 `backend/app/services/copywriting.py`의 로컬 규칙으로 대체합니다.
- `copyMode=preserve`이고 사용자가 `userCopy`를 입력한 경우, 사용자 문구 보존을 우선해 별도 문구 AI 호출 없이 기본 정리 규칙을 적용합니다.
- `adCopyEnabled=true`이면 문구 결과를 이미지 생성 프롬프트에 넣어 이미지 모델이 광고 이미지 안에 직접 렌더링하도록 지시합니다.
- `adCopyEnabled=false`이면 임의 문구, 가격표, 로고, 워터마크를 만들지 않도록 프롬프트에서 금지합니다.

## Logo Policy

- 로고는 백엔드에서 픽셀 후처리로 붙이지 않습니다.
- `logoDataUrl`이 있으면 메뉴 이미지와 함께 OpenAI Images Edit API의 두 번째 reference image로 전달합니다.
- `logoPosition`은 이미지 모델에게 로고 배치 위치를 지시하는 값입니다.
- 이 방식은 광고 이미지 전체 톤에 맞춘 자연스러운 반영에 유리하지만, 로고의 픽셀 단위 완전 보존을 보장하지는 않습니다.

## Image Policy

- 프론트/백엔드 공통 허용 형식은 JPG, PNG, WEBP입니다.
- 백엔드는 파일 시그니처와 실제 디코딩 가능 여부를 검증합니다.
- OpenAI에는 원본을 직접 보내지 않고, EXIF 방향 보정 후 PNG/RGB로 정규화한 이미지를 보냅니다.
- OpenAI 응답 이미지는 선택한 상세 광고 규격의 `targetWidth` x `targetHeight` 크기로 후처리됩니다.
- `cover`는 캔버스를 꽉 채우고 중앙 기준으로 일부를 자를 수 있습니다.
- `contain`은 원본 전체를 보존하고 남는 영역을 흐림 배경으로 채웁니다.

## Storage

- `STORAGE_BACKEND=local`이면 업로드 원본과 결과 이미지를 `backend/uploads`, `backend/outputs`에 저장합니다.
- `STORAGE_BACKEND=r2`이면 Cloudflare R2 버킷에 저장하고, `R2_PUBLIC_URL` 기반 URL을 응답합니다.
- DB에는 환경별 절대 URL 대신 저장소 path/key를 남겨 배포 환경이 바뀌어도 기록을 재사용할 수 있게 합니다.
- `/outputs`와 `/uploads`는 local 저장소 결과를 프론트에서 접근할 수 있도록 정적 경로로 마운트합니다.

## Database / Migrations

- 운영/데모/배포 DB는 PostgreSQL 또는 Supabase Postgres 기준입니다.
- 운영·공유 DB 스키마는 Alembic으로 관리합니다.
- 새 DB를 연결하거나 마이그레이션이 추가되면 백엔드 실행 전에 `uv run alembic upgrade head`를 적용합니다.
- `DATABASE_URL`이 없으면 앱은 실행되지 않습니다.
- SQLite는 pytest 격리 테스트처럼 `ALLOW_SQLITE_DATABASE=true`를 명시한 경우에만 허용합니다.
- `backend.app.db.database.async_init_db()`는 테스트용 보조 함수이며, 운영 테이블 자동 생성 용도로 사용하지 않습니다.

## Run

```bash
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

## Test

```bash
uv sync --all-groups
uv run ruff check .
uv run pytest -p no:cacheprovider
uv run python -m compileall backend frontend tests
```

## Key Files

```text
backend/
  main.py                         과거 실행 경로 호환용 진입점
  app/main.py                     FastAPI 앱과 API 라우트
  app/schemas.py                  요청/응답 스키마
  app/core/config.py              환경변수 기반 런타임 설정
  app/core/presets.py             config/presets.json 로딩
  app/core/prompts.py             이미지 생성 프롬프트 조립
  app/core/auth.py                Supabase JWT 검증
  app/api/                        인증, 내부 점검, 미들웨어 라우트
  app/db/                         생성 기록, 캐시, 사용량 추적 DB 계층
  app/services/generation_service.py  이미지 생성 전체 흐름 조립
  app/services/openai_copy.py         OpenAI 텍스트 모델로 광고 문구 생성/수정
  app/services/copywriting.py         mock/대체 경로용 광고 문구 정리
  app/services/generation_copy.py     캐시·DB 저장용 광고 문구 메타데이터 조립
  app/services/image_validation.py    업로드 이미지 검증
  app/services/image_processing.py    OpenAI 입력 정규화와 최종 리사이즈
  app/services/openai_images.py       OpenAI Images API 호출
  app/services/generation_storage.py  local/R2 저장 경로 준비와 결과 저장
  app/services/storage/               local/R2 저장소 구현
  app/services/storage_url.py         저장소별 이미지 접근 URL 생성
```

## Notes

- 실제 API 키, DB URL, R2 키는 저장소에 커밋하지 않습니다.
- GCP, Railway 등 배포 시 비밀값은 Secret Manager나 Variables UI로 주입합니다.
- `prompt` 응답은 production 환경에서 노출하지 않습니다.
- 로고는 reference image 기반 반영이므로 완전한 원본 로고 합성이 필요하면 별도 후처리 방식 검토가 필요합니다.
