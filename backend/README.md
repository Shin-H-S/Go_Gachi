# Go_Gachi Backend

소상공인 광고 이미지 제작 서비스의 FastAPI 백엔드입니다.
현재 API는 사용자가 업로드한 이미지 data URL, 프리셋 ID, 추가 요청 문구를 받아 광고용 이미지로 편집하는 MVP 흐름을 기준으로 합니다.

## Runtime

- Python `3.11.14`
- 패키지 관리: `uv`
- 기본 실행 앱: `backend.app.main:app`

GCP/Cloud Run 배포를 우선 지원하지만, 테스트와 검증을 위해 같은 앱을 로컬 환경에서도 실행할 수 있게 구성합니다.

## Main API

| Method | Path | Description |
| --- | --- | --- |
| GET | `/` | 서비스 기본 상태 |
| GET | `/api/health` | 외부 의존성 없는 헬스체크 |
| GET | `/api/ready` | 설정과 프리셋 로딩 상태 확인 |
| GET | `/api/config` | 프론트 초기 설정용 프리셋 목록 |
| POST | `/api/generate` | 이미지 편집 생성 요청 |

## Generate Request

현재 스키마는 JSON 요청만 사용합니다.
V3 요청 필드는 확장되어 있으며, 현재는 문구 처리 결과(`copy`)까지 응답합니다.
`adCopyEnabled=true`이면 문구 처리 결과를 이미지 생성 프롬프트에 포함해 광고 이미지 안에 함께 생성합니다.
로고 합성은 후속 기능 브랜치에서 연결합니다.

```json
{
  "imageDataUrl": "data:image/png;base64,...",
  "presetId": "instagram",
  "detailType": "story_image",
  "userPrompt": "광고 유형: 스토리 이미지\n오늘 아메리카노 2,500원",
  "copyMode": "preserve",
  "adCopyEnabled": false,
  "logoDataUrl": null,
  "logoPosition": "bottom_right",
  "parentRequestId": null,
  "targetWidth": 1080,
  "targetHeight": 1920,
  "resizeMode": "cover"
}
```

- `imageDataUrl`: JPG, PNG, WEBP data URL.
  백엔드는 파일 시그니처와 실제 디코딩 가능 여부를 확인한 뒤, OpenAI 호출 전
  입력 이미지를 PNG/RGB로 정규화합니다.
- `presetId`: `GET /api/config`에서 받은 프리셋 ID. 생략하면 기본 프리셋 사용
- `detailType`: 프리셋 안의 상세 광고 유형 ID. 채널·상세 유형별 전용 프롬프트를 고르는 데 사용
- `userPrompt`: V3 사용자 요청/광고 문구입니다.
- `copyMode`: 문구 처리 방식. `preserve`, `polish`, `rewrite` 중 하나이며 기본값은 `preserve`입니다.
- `adCopyEnabled`: 광고 문구 사용 여부입니다. true이면 `copy` 응답을 구성하고 이미지 생성 프롬프트에 문구를 포함합니다.
- `logoDataUrl`: 로고 반영에 사용할 JPG, PNG, WEBP data URL입니다. 값이 있으면 메뉴 이미지와 함께 OpenAI 이미지 편집 API의 reference image로 전달합니다.
- `logoPosition`: 로고 위치. `top_left`, `top_right`, `bottom_left`, `bottom_right`, `center_bottom` 중 하나이며 기본값은 `bottom_right`입니다.
- `parentRequestId`: 수정 이력 연결용 부모 생성 ID입니다. 현재 브랜치에서는 스키마만 열어둡니다.
- `targetWidth`, `targetHeight`: 사용자가 선택한 상세 광고 규격의 최종 출력 픽셀 크기.
  둘 중 하나만 보낼 수 없으며, 생략하면 선택한 상세 광고 유형의 기본 크기를 사용합니다.
- `resizeMode`: 최종 후처리 방식. 기본값은 `cover`입니다.
  `cover`는 캔버스를 꽉 채우고 중앙 기준으로 일부를 자를 수 있으며,
  `contain`은 원본 전체를 보존하고 남는 영역을 흐림 배경으로 채웁니다.

알 수 없는 `presetId`는 연동 오류를 빨리 발견할 수 있도록 `400`으로 응답합니다.

## Generate Response

```json
{
  "imageDataUrl": "data:image/png;base64,...",
  "provider": "openai",
  "preset": {
    "id": "instagram",
    "label": "인스타그램"
  },
  "copy": null,
  "logo": null,
  "revision": null,
  "note": null,
  "prompt": null
}
```

- `prompt`: `APP_ENV=production`에서는 내부 프롬프트 보호를 위해 `null`로 응답합니다.
  `local`/`dev` 환경에서는 디버깅을 위해 생성에 사용한 프롬프트가 포함될 수 있습니다.
- 응답 `imageDataUrl`의 PNG는 `targetWidth` x `targetHeight` 크기로 후처리되어 반환됩니다.
- `copy`: `adCopyEnabled=true`일 때 문구 처리 결과를 내려줍니다. OpenAI 생성 경로에서는 이 문구를 이미지 생성 프롬프트에 포함합니다.
- `logo`: 로고 이미지를 요청에 포함한 경우 사용 여부와 위치를 내려줍니다.
- `revision`: V3 후속 브랜치에서 수정 이력 처리 결과를 채울 예정입니다.

## Copy Composition

- 문구 생성은 `backend/app/services/openai_copy.py`에서 OpenAI 텍스트 모델을 우선 사용합니다.
- OpenAI 키가 없거나 mock 모드이면 `backend/app/services/copywriting.py`의 기본 규칙으로 대체합니다.
- OpenAI 이미지 생성 경로에서는 생성된 문구를 최종 이미지 프롬프트에 포함해 한 번에 광고 이미지를 만듭니다.

## Upload Policy

- 프론트/백엔드 공통 허용 형식은 JPG, PNG, WEBP입니다.
- 업로드 원본은 감사와 재현을 위해 `backend/uploads`에 그대로 저장합니다.
- OpenAI에는 원본을 직접 보내지 않고, EXIF 방향 보정 후 PNG/RGB로 변환한 이미지를 보냅니다.
- OpenAI 입력 이미지 로그에는 MIME, 포맷, 모드, 크기, 정규화 후 바이트 수만 남기고 API 키나 프롬프트는 남기지 않습니다.

## Database / Migrations

- 운영/데모/배포 DB는 PostgreSQL(Supabase) 기준입니다.
- 운영·공유 DB 스키마는 Alembic으로 관리합니다.
- 새 DB를 연결하거나 마이그레이션이 추가되면 백엔드 실행 전에 `uv run alembic upgrade head`를 적용합니다.
- `backend.app.db.database.async_init_db()`는 pytest 격리 테스트용 보조 함수입니다. 앱 시작 시 운영 테이블을 자동 생성하는 용도로 사용하지 않습니다.

## Key Files

```text
backend/
  app/main.py                 FastAPI 앱과 API 라우트
  app/schemas.py              현재 요청/응답 스키마
  app/core/config.py          환경변수 기반 런타임 설정
  app/core/presets.py         config/presets.json 로딩
  app/core/prompts.py         이미지 편집 프롬프트 조립
  app/services/image_edit.py          기존 import 호환용 이미지 생성 진입점
  app/services/generation_service.py  이미지 생성 전체 흐름 조립
  app/services/openai_copy.py         OpenAI 텍스트 모델로 광고 문구 생성/수정
  app/services/copywriting.py         mock/대체 경로용 광고 문구 정리
  app/services/image_validation.py    업로드 이미지 검증
  app/services/image_processing.py    OpenAI 입력 정규화와 최종 리사이즈
  app/services/openai_images.py       OpenAI Images API 호출
  app/services/image_types.py         이미지 처리 공통 타입
  app/db/                     생성 기록, 캐시, 사용량 추적 DB 계층
```

## Notes

- 실제 API 키는 저장소에 커밋하지 않습니다.
- GCP 배포 시 `OPENAI_API_KEY`는 Secret Manager를 통해 주입합니다.
- `DATABASE_URL`은 PostgreSQL 연결 문자열로 설정해야 합니다. SQLite는 실제 실행용 DB로 사용하지 않습니다.
