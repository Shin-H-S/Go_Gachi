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
업종, 분위기, 광고 유형, 목적 등 세분화된 프롬프트 변수는 이후 API 버전업에서 추가할 예정입니다.

```json
{
  "imageDataUrl": "data:image/png;base64,...",
  "presetId": "instagram_square",
  "detailType": "story_image",
  "feedback": "광고 유형: 스토리 이미지\n밝고 따뜻한 카페 광고 느낌으로 만들어줘",
  "targetWidth": 1080,
  "targetHeight": 1920
}
```

- `imageDataUrl`: PNG, JPG, WEBP data URL
- `presetId`: `GET /api/config`에서 받은 프리셋 ID. 생략하면 기본 프리셋 사용
- `detailType`: 프리셋 안의 상세 광고 유형 ID. 채널·상세 유형별 전용 프롬프트를 고르는 데 사용
- `feedback`: 사용자 추가 요청 문구
- `targetWidth`, `targetHeight`: 사용자가 선택한 상세 광고 규격의 최종 출력 픽셀 크기.
  둘 중 하나만 보낼 수 없으며, 생략하면 프리셋 기본 크기를 사용합니다.

알 수 없는 `presetId`는 연동 오류를 빨리 발견할 수 있도록 `400`으로 응답합니다.

## Generate Response

```json
{
  "imageDataUrl": "data:image/png;base64,...",
  "provider": "openai",
  "preset": {
    "id": "instagram_square",
    "label": "인스타그램"
  },
  "note": null,
  "prompt": null
}
```

- `prompt`: `APP_ENV=production`에서는 내부 프롬프트 보호를 위해 `null`로 응답합니다.
  `local`/`dev` 환경에서는 디버깅을 위해 생성에 사용한 프롬프트가 포함될 수 있습니다.
- 응답 `imageDataUrl`의 PNG는 `targetWidth` x `targetHeight` 크기로 후처리되어 반환됩니다.

## Database / Migrations

- 운영·공유 DB 스키마는 Alembic으로 관리합니다.
- 새 DB를 연결하거나 마이그레이션이 추가되면 백엔드 실행 전에 `uv run alembic upgrade head`를 적용합니다.
- `backend.app.db.database.async_init_db()`는 테스트와 임시 개발 DB 보조용입니다. 앱 시작 시 운영 테이블을 자동 생성하는 용도로 사용하지 않습니다.

## Key Files

```text
backend/
  app/main.py                 FastAPI 앱과 API 라우트
  app/schemas.py              현재 요청/응답 스키마
  app/core/config.py          환경변수 기반 런타임 설정
  app/core/presets.py         config/presets.json 로딩
  app/core/prompts.py         이미지 편집 프롬프트 조립
  app/services/image_edit.py  이미지 검증, 캐시, OpenAI 호출 흐름
  app/db/                     생성 기록, 캐시, 사용량 추적 DB 계층
```

## Notes

- 실제 API 키는 저장소에 커밋하지 않습니다.
- GCP 배포 시 `OPENAI_API_KEY`는 Secret Manager를 통해 주입합니다.
- 기본 DB는 SQLite지만, 운영 저장소가 필요하면 Cloud SQL/PostgreSQL 전환을 고려합니다.
