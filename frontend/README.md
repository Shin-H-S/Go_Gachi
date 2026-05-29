# Frontend

카페 메뉴 광고 이미지 제작용 Streamlit 프론트엔드입니다.
이미지 업로드, 광고 채널 선택, 프롬프트 입력, 생성 중 로딩 UI, 결과 미리보기를 제공합니다.

## Folder Structure

```text
frontend/
  app.py                # Streamlit 프론트엔드 진입점
  app/                  # 향후 컴포넌트 분리용 폴더
    components/         # 재사용 UI 컴포넌트 작성 위치
  assets/               # 샘플 이미지, 아이콘 등 정적 리소스
  tests/                # 프론트엔드 테스트 코드
  .env.example          # 배포된 백엔드 URL 예시
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

## Backend Connection

프론트엔드는 배포된 백엔드 Cloud Run URL을 `BACKEND_URL`로 받아 호출합니다.

```env
BACKEND_URL=https://YOUR_BACKEND_CLOUD_RUN_URL
```

현재 백엔드 MVP에서 우선 연동할 API는 아래와 같습니다.

- `GET /api/config`: 광고 프리셋 목록 조회
- `POST /api/generate`: `imageDataUrl`, `presetId`, `feedback`, `targetWidth`, `targetHeight`를 전달해 생성 요청

`targetWidth`와 `targetHeight`는 사용자가 선택한 상세 광고 유형의 최종 다운로드 크기입니다.
백엔드는 생성 결과를 이 크기의 PNG로 맞춰 반환합니다.

`BACKEND_URL`이 없으면 프론트 화면 확인을 위해 mock 결과 이미지를 표시합니다.
