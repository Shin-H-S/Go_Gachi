# Go_Gachi 백엔드 (FastAPI)

소상공인 광고 생성 서비스의 백엔드. 사진 + 광고 정보를 받아 OpenAI(gpt-image-1-mini)로
광고 이미지 1장을 생성하고, 결과 이미지를 파일로 저장해 URL로 돌려준다.

## 사전 요구사항

- **Python 3.11+** & **uv** (패키지 관리)
- **OpenAI API Key** (이미지 생성용)

## 셋업 (처음 한 번)

```bash
cd backend

# 1) 환경변수 파일 만들기 (양식 복사 후 본인 값 채우기)
#    Windows PowerShell:
Copy-Item .env.example .env
#    macOS/Linux:
#    cp .env.example .env
#  → .env 열어서 OPENAI_API_KEY 를 본인 키로 채운다 (sk- 로 시작)

# 2) 파이썬 패키지 설치
uv sync          # 또는: pip install -r requirements.txt
```

## 실행

```bash
cd backend
uvicorn main:app --reload
```

확인:
- 서버 상태: http://127.0.0.1:8000/api/v1/health
- API 문서(테스트 가능): http://127.0.0.1:8000/docs

## API

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| GET | `/api/v1/health` | 서버 상태 + OpenAI 키 설정 여부 |
| POST | `/api/v1/generate` | 사진 + 광고 정보 → 광고 이미지 1장 생성 |

`/generate` 입력(multipart/form-data): `image`(파일), `industry`, `mood`, `ad_type`,
`objective`, `placement`(기본 `instagram_feed`) 등. 결과는 `image_url`로 받은 경로를
붙여 미리보기 한다. 생성된 이미지는 `/outputs/<파일명>.png`로 정적 제공된다.

## 디렉토리 구조

```
backend/
├── main.py                 앱 시작점 (create_app: 라우터/CORS/정적 경로)
├── .env / .env.example     환경변수 (.env 는 git 제외)
├── uploads/ outputs/       원본/결과 이미지 (git 제외)
└── app/
    ├── core/config.py        환경설정 (pydantic-settings, .env 로드)
    ├── api/endpoints.py      라우트: /health, /generate
    ├── models/schemas.py     요청/응답 형태 (Pydantic)
    ├── services/pipeline.py  생성 흐름 전체 조율
    ├── ml/text_gen.py        프롬프트(지시문) 생성
    ├── ml/image_gen.py       OpenAI 이미지 생성 호출
    ├── ml/image_utils.py     이미지 검증·사이즈 계산·리사이즈
    ├── storage/files.py      파일 저장/URL 생성
    └── db/                   (placeholder) DB는 추후 재도입 예정
```

## 주의

- **`.env` 는 절대 git 에 올리지 않는다** (API 키 노출 금지). 이미 `.gitignore` 처리됨.
- 새 패키지 설치 시: `uv add <패키지>` → 팀원도 `uv sync` 로 동일 환경.
- DB는 현재 MVP 범위 밖이라 제거됨. 히스토리/수정요청 기능을 붙일 때 재도입 예정
  (이전 구현은 git 커밋 `b57d91a`에 보존).
