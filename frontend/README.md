# Streamlit Upload UI

카페 메뉴 광고 이미지 제작용 Streamlit 프론트엔드입니다.
이미지 업로드, 광고 채널 선택, 프롬프트 입력, 생성 중 로딩 UI, 결과 미리보기를 제공합니다.

## Structure

```text
frontend/
  app.py                # Streamlit 프론트엔드 진입점
  app/                  # 향후 컴포넌트 분리용 폴더
    components/         # 재사용 UI 컴포넌트 작성 위치
  assets/               # 샘플 이미지, 아이콘 등 정적 리소스
  tests/                # 프론트엔드 테스트 코드
  .env.example          # 배포된 백엔드 URL 예시
  requirements.txt      # Streamlit 개발 시작용 의존성
```

## Run

레포 루트에서 프론트 의존성을 설치한 뒤 실행합니다.

```bash
pip install -r requirements-frontend.txt
streamlit run frontend/app.py
```

## Backend Connection

프론트엔드는 배포된 백엔드 Cloud Run URL을 `BACKEND_URL`로 받아 호출합니다.

```env
BACKEND_URL=https://YOUR_BACKEND_CLOUD_RUN_URL
```

- `GET /api/config`: 광고 프리셋 목록 조회
- `POST /api/generate`: `imageDataUrl`, `presetId`, `feedback`을 전달해 생성 요청

`BACKEND_URL`이 없으면 프론트 화면 확인을 위해 mock 결과 이미지를 표시합니다.
