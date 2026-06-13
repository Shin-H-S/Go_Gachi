# Frontend

카페 메뉴 광고 이미지 제작용 Streamlit 프론트엔드입니다.
이미지 업로드, 광고 채널 선택, 프롬프트 입력, 생성 중 로딩 UI, 결과 미리보기를 제공합니다.

## Folder Structure

```text
frontend/
  app.py                # Streamlit entrypoint
  pages/                # Page renderers such as main and work
  core/                 # Config loading and routing helpers
  services/             # Backend API boundary
  work/                 # Work-page state, components, preview, generation, uploads
  media/                # Image helpers and preview canvas
  css/                  # CSS fragments composed by styles.py
  assets/               # Channel/sample image assets
  styles.py             # CSS composer and injector
  api_client.py         # Compatibility alias to services/api_client.py
  config.py             # Compatibility alias to core/config.py
  router.py             # Compatibility alias to core/router.py
  upload_utils.py       # Compatibility alias to work/uploads.py
  image_utils.py        # Compatibility alias to media/image_utils.py
  .env.example          # Frontend env example
```

## Run

레포 루트에서 프론트 의존성을 설치한 뒤 실행합니다.
작업 전 또는 의존성이 바뀐 뒤에는 먼저 `uv sync --group frontend`를 실행합니다.

```bash
uv sync --group frontend
uv run streamlit run frontend/app.py
```

## Preset Rule

광고 채널과 규격은 레포 루트의 `config/presets.json`을 기준으로 맞춥니다.
프론트에서 백엔드로 보내는 `presetId`는 `config/presets.json`의 `id`와 반드시 일치해야 합니다.

## Upload Policy

- 프론트 업로드 허용 확장자는 `frontend/upload_utils.py`의 `UPLOAD_FILE_TYPES`에서 관리합니다.
- 현재 허용 형식은 JPG, PNG, WEBP입니다.
- 백엔드는 업로드 원본을 검증한 뒤 OpenAI 호출 전 PNG/RGB로 정규화하므로, 프론트는 별도 이미지 변환을 하지 않습니다.

## Backend Connection

프론트엔드는 레포 최상단 `.env`를 먼저 읽고, `frontend/.env`가 있으면 프론트 전용
설정으로 덮어씁니다. 기본 백엔드 주소는 같은 서버에서 실행 중인 FastAPI입니다.

```env
BACKEND_URL=http://127.0.0.1:8000
```

배포된 백엔드나 별도 서버를 바라봐야 하면 `BACKEND_URL`만 해당 주소로 바꿉니다.
광고 채널/상세 유형 프리셋은 기본적으로 백엔드 `/api/config`를 먼저 읽고, 백엔드가 아직
준비되지 않은 경우 로컬 `config/presets.json`으로 화면을 구성합니다.

```env
FRONTEND_CONFIG_SOURCE=auto
```

값을 `backend`로 두면 백엔드 config만 사용하고, `local`로 두면 로컬 파일만 사용합니다.

현재 백엔드 MVP에서 우선 연동할 API는 아래와 같습니다.

- `GET /api/config`: 광고 프리셋 목록 조회
- `POST /api/generate`: `imageDataUrl`, `presetId`, `detailType`, `userPrompt`, `userCopy`, `targetWidth`, `targetHeight`를 전달해 생성 요청

`detailType`은 사용자가 선택한 상세 광고 유형 ID입니다.
`targetWidth`와 `targetHeight`는 사용자가 선택한 상세 광고 유형의 최종 다운로드 크기입니다.
백엔드는 생성 결과를 이 크기의 PNG로 맞춰 저장하고, 응답에서는 `imageUrl`을 우선 내려줍니다.
`imageDataUrl`은 mock/fallback 응답에서만 사용할 수 있으므로 프론트는 `imageUrl` 우선,
`imageDataUrl` fallback 순서로 처리합니다.

백엔드 연결 실패 시에는 로컬 성공 결과로 대체하지 않고 에러 메시지를 표시합니다.
