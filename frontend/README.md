# Frontend

Streamlit 프론트엔드 개발자가 작업을 시작할 수 있도록 남겨둔 초기 폴더입니다.
현재 백엔드 PR에서는 프론트 구현 코드를 포함하지 않습니다.

## Folder Structure

```text
frontend/
  app/                  # Streamlit 앱 코드 작성 위치
    components/         # 재사용 UI 컴포넌트 작성 위치
  assets/               # 샘플 이미지, 아이콘 등 정적 리소스
  tests/                # 프론트엔드 테스트 코드
  .env.example          # 배포된 백엔드 URL 예시
  requirements.txt      # Streamlit 개발 시작용 의존성
```

## Backend Connection

프론트엔드는 배포된 백엔드 Cloud Run URL을 `BACKEND_URL`로 받아 호출합니다.

```env
BACKEND_URL=https://YOUR_BACKEND_CLOUD_RUN_URL
```

현재 백엔드 MVP에서 우선 연동할 API는 아래와 같습니다.

- `GET /api/config`: 광고 프리셋 목록 조회
- `POST /api/generate`: 이미지와 광고 조건을 전달해 생성 요청

세부 UI 구성과 Streamlit 구현 방식은 프론트엔드 담당자가 이 폴더 안에서 이어서 작성합니다.
