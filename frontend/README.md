# Frontend

Streamlit 기반 프론트엔드 작업 공간입니다. 이 저장소에서는 로컬 실행을 기준으로 하지 않고, 배포된 백엔드 Cloud Run URL을 호출하는 구조로 개발합니다.

## Suggested Structure

```text
frontend/
  app/
    app.py              # Streamlit entrypoint
    api.py              # FastAPI backend client
    state.py            # session state helpers
    components/         # reusable UI blocks
  assets/               # sample images, UI assets
  tests/                # frontend-side tests
  .env.example
  requirements.txt
```

## Backend API

Set `BACKEND_URL` to the deployed backend URL.

```env
BACKEND_URL=https://YOUR_BACKEND_CLOUD_RUN_URL
```

- `GET /api/config`: preset 목록 조회
- `POST /api/generate`: 이미지 data URL, presetId, feedback 전송

Generate request example:

```json
{
  "imageDataUrl": "data:image/png;base64,...",
  "presetId": "instagram_square",
  "feedback": "조금 더 밝고 따뜻하게"
}
```

Generate response example:

```json
{
  "imageDataUrl": "data:image/png;base64,...",
  "provider": "openai",
  "preset": {
    "id": "instagram_square",
    "label": "Instagram Feed"
  },
  "note": null,
  "prompt": "..."
}
```
