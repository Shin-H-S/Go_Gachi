# Go_Gachi

소상공인을 위한 AI 광고 이미지 제작 서비스입니다. 사용자가 업로드한 이미지를 업종, 분위기, 광고 유형, 목적, 게시 위치에 맞게 재구성하고 플랫폼 규격 이미지로 저장하는 흐름을 목표로 합니다.

## Backend baseline

FastAPI 앱은 `backend/main.py`에서 시작합니다.

```powershell
cd backend
Copy-Item .env.example .env
..\.venv\Scripts\uvicorn.exe main:app --reload --port 8000
```

### Environment

`backend/.env`에 최소한 아래 값을 설정합니다.

```env
OPENAI_API_KEY=sk-...
OPENAI_IMAGE_MODEL=gpt-image-1-mini
```

### Endpoints

- `GET /api/v1/health`: 서버 상태와 OpenAI 키 설정 여부 확인
- `POST /api/v1/generate`: `multipart/form-data`로 이미지와 광고 브리프를 받아 결과 이미지를 생성

`POST /api/v1/generate` form fields:

- `image`: 업로드 이미지 파일, `jpeg/png/webp`
- `industry`: 업종
- `mood`: 원하는 분위기
- `ad_type`: 광고 유형
- `objective`: 광고 목적
- `placement`: `instagram_feed`, `instagram_story`, `instagram_reels`, `facebook_feed`, `naver_place`, `naver_blog`, `kakao_channel`, `banner_landscape`, `custom`
- `brand_name`, `target_audience`, `key_message`, `offer`: 선택 입력
- `custom_width`, `custom_height`: `placement=custom`일 때 필요

생성 결과는 `backend/outputs`에 저장되고 `/outputs/{filename}` 경로로 제공됩니다.
