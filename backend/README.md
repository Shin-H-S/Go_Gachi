# Go_Gachi 백엔드 (FastAPI)

소상공인 광고 생성 서비스의 백엔드. 사진 + 매장정보를 받아 광고 문구/이미지를 생성하고, 결과를 MySQL에 저장한다.

## 사전 요구사항

- **Docker Desktop** (MySQL 컨테이너 실행용)
- **Python 3.11+** & **uv** (패키지 관리)

## 셋업 (처음 한 번)

```bash
cd backend

# 1) 환경변수 파일 만들기 (양식 복사 후 본인 값 채우기)
#    Windows PowerShell:
Copy-Item .env.example .env
#    macOS/Linux:
#    cp .env.example .env
#  → .env 열어서 OPENAI_API_KEY, DB_PASSWORD 등을 채운다

# 2) MySQL 컨테이너 띄우기
docker compose up -d

# 3) 파이썬 패키지 설치
uv sync          # 또는: pip install -r requirements.txt
```

## 실행

```bash
cd backend
uvicorn main:app --reload
```

확인:
- 서버 상태: http://127.0.0.1:8000/health → `{"status":"ok"}`
- API 문서(테스트 가능): http://127.0.0.1:8000/docs

## 자주 쓰는 명령

| 명령 | 설명 |
| --- | --- |
| `docker compose up -d` | MySQL 켜기 (백그라운드) |
| `docker compose down` | MySQL 끄기 (데이터 유지) |
| `docker compose down -v` | MySQL 끄기 + **데이터 삭제** |
| `docker stats gogachi_mysql` | MySQL 자원 사용량 보기 |
| `uvicorn main:app --reload` | 서버 실행 (코드 변경 시 자동 재시작) |

## DB 접속 정보 (기본값)

| 항목 | 값 |
| --- | --- |
| host | 127.0.0.1 |
| port | **3307** (3306 아님 — 충돌 회피) |
| user | root |
| password | `.env` 의 `DB_PASSWORD` |
| database | go_gachi |

DBeaver 등 DB 툴로 위 정보로 접속하면 테이블을 직접 볼 수 있다.

## 디렉토리 구조

```
backend/
├── main.py                 앱 시작점 (라우터/CORS/시작 시 폴더·DB 준비)
├── docker-compose.yml      MySQL 컨테이너 정의
├── .env / .env.example     환경변수 (.env 는 git 제외)
├── uploads/ outputs/       원본/결과 이미지 (git 제외)
└── app/
    ├── core/config.py      환경설정 (.env 로드)
    ├── api/endpoints.py    라우트: /health, /generate
    ├── models/schemas.py   요청/응답 형태 (Pydantic)
    ├── ml/text_gen.py      광고 문구 생성 (OpenAI 연동 예정)
    ├── ml/image_gen.py     이미지 생성 (OpenAI GPT-image API 예정)
    ├── storage/files.py    이미지 저장
    └── db/                 MySQL 연결/모델/저장 (SQLAlchemy)
```

## 주의

- **`.env` 는 절대 git 에 올리지 않는다** (API 키·DB 비번 노출 금지). 이미 `.gitignore` 처리됨.
- 새 패키지 설치 시: `uv add <패키지>` → 팀원도 `uv sync` 로 동일 환경.
