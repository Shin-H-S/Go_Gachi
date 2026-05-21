# 백엔드 설계안 — AdMate AI Studio (Go_Gachi)

- 작성일: 2026-05-20
- 담당: YJ (백엔드 / 서비스 개발)
- 상태: 초안 (팀 확인 필요 항목 표시)

## 1. 서비스 개요

소상공인이 **상품 사진 + 간단한 정보**를 입력하면 AI가 **광고 문구와 광고 이미지**를 생성해주는 서비스.

장기적으로는 "수정 요청 → 재생성"을 이어가는 대화형 흐름(예: "더 밝게", "문구 빼줘")을 지향하지만,
**이번 단계는 단발 생성(한 번 입력 → 한 번 생성)에 집중**한다.
세션 기억·수정 재생성은 복잡도가 높아 **고도화로 남긴다.** 생성 결과는 DB에 저장한다(기록/다운로드용).

## 2. 전체 서비스 흐름

```
프론트엔드(미정: Streamlit 후보)
   │  이미지 + 상품정보 + 분위기 + 수정요청
   ▼
백엔드 (FastAPI, 중앙 허브)
   ├─ 이미지 저장
   ├─ OpenAI: 광고 문구 + 이미지 생성 프롬프트 + 수정요청 해석
   ├─ 이미지 생성 (OpenAI Image API)
   ├─ DB 저장 (세션/생성기록)
   └─ 결과 반환
   ▼
프론트엔드: 문구 + 이미지 출력, 수정요청 입력, 다운로드
```

## 3. MVP 범위

### 포함
- 상품 사진 업로드
- **선택형**: 업종, 광고 목적, 분위기, 출력 용도
- **자유입력**: 매장명, 가격, 연락처
- 광고 문구 생성 (OpenAI)
- 광고 이미지 생성 (**OpenAI Image API**)
- 결과 출력 + 이미지 다운로드 (생성 기록 DB 저장)

> **분야(업종) 전략**: 우선 **카페**만 제대로 만들고(프롬프트 템플릿 1종), 이후 다른 업종을 점차 추가.
> 업종 추가 = 템플릿 한 칸 추가일 뿐, 코드 구조는 안 바뀜.

### 제외 (이번 MVP에서 안 함)
- 회원가입/로그인, 결제
- 복잡한 이미지 편집기
- 사용자별 장기 히스토리
- 임베딩 / RAG
- vLLM / Triton 직접 서빙 (텍스트는 OpenAI API 사용)
- **세션 기억 + 수정 요청 재생성(/revise)** — 복잡도 높아 **고도화로 미룸**
- **HuggingFace 이미지 모델 직접 서빙** — 이번엔 OpenAI Image API 사용, HF는 **고도화로 미룸**

## 4. 5/21 베이스라인 범위 (확정)

내일 목표 = **"동작하는 뼈대 + DB"**. 전체 MVP는 이후 단계적으로.

| 단계 | 내용 |
| --- | --- |
| **베이스라인 (5/21)** | 서버 실행, `/health`, `/generate`(이미지·정보 받아 저장 + **비용 방지용 더미 광고 문구 응답**), **Docker MySQL 띄우기 + sessions/generations 저장** |
| 다음 | OpenAI 광고 문구 실제 생성 연동, 이미지 생성(OpenAI Image API) 연동 |
| 고도화 | `/revise` 수정요청 재생성(messages 테이블), 배경제거/리사이즈, 캐싱, $30 사용량 모니터링 |

## 5. 디렉토리 구조

```
backend/
├── main.py                 FastAPI 앱 시작점 (라우터, CORS, 시작 시 폴더/DB 준비)
├── docker-compose.yml      MySQL 컨테이너 (추후 백엔드도)
├── .env / .env.example     비밀값 (DB 접속정보, OPENAI_API_KEY)
├── uploads/ outputs/       원본/결과 이미지 (.gitkeep, 내용물 git 제외)
└── app/
    ├── core/config.py      환경설정 (.env 로드)
    ├── models/schemas.py   요청/응답 형태 (Pydantic)
    ├── api/endpoints.py     /health, /generate, (후속) /revise
    ├── services/pipeline.py 생성/수정 흐름 조립
    ├── ml/text_gen.py       OpenAI: 문구 + 이미지 프롬프트 + 수정요청 해석
    ├── ml/image_gen.py      이미지 생성 (OpenAI Image API, 교체 가능 구조 / HF는 고도화)
    ├── ml/image_utils.py    (후속) 배경제거/리사이즈
    ├── storage/files.py     이미지 저장 + 파일명 규칙
    └── db/
        ├── database.py      MySQL 연결 (SQLAlchemy)
        ├── models.py        sessions / messages / generations 테이블
        └── crud.py          저장·조회 로직
```

## 6. API 계약

### `GET /health`
- 응답: `{"status": "ok"}` — 서버 상태 확인

### `POST /generate` (첫 생성, multipart)

입력은 **선택형(클릭/드롭다운)** 과 **자유입력(텍스트)** 으로 구분한다.

요청:
| 필드 | 입력 방식 | 타입 | 필수 |
| --- | --- | --- | --- |
| image | 파일 업로드 | 파일 | ✅ |
| industry(업종) | **선택형** | str | ✅ |
| ad_purpose(광고목적) | **선택형** | str | 선택 |
| mood(분위기) | **선택형** | str | 선택 |
| output_type(출력용도) | **선택형** | str | 선택 |
| store_name(매장명) | 자유입력 | str | ✅ |
| price(가격) | 자유입력 | str | 선택 |
| contact(연락처) | 자유입력 | str | 선택 |

선택형 옵션:
- **업종**: 카페(우선) → 이후 확장
- **광고 목적**: 신규 오픈 홍보 / 이벤트·할인 안내 / 신메뉴 출시 / 예약 유도 / 후기 강조 / 전문성 강조 / 고급 이미지 브랜딩 / 명절·시즌 이벤트
- **분위기**: 깔끔한 / 고급스러운 / 따뜻한 / 젊고 트렌디한 / 믿음 가는 전문적인 / 저렴하고 실속 있는
- **출력 용도**: 인스타 피드 4:5 / 인스타 스토리 9:16 / 네이버 블로그 썸네일 / 카카오톡 채널 / 당근마켓 동네광고 / 오픈 이벤트 배너 / 가격표 이미지 / 후기 카드뉴스

> **프롬프트 조립은 별도 담당(프롬프트 담당)의 영역.** 백엔드는 위 선택값/입력값을 모아 전달하고,
> 프롬프트 생성 함수(`ml/text_gen.py`)는 **인터페이스(자리)만** 만들어 둔다. 베이스라인에선 간단한 더미로 시작.

응답 (JSON):
| 필드 | 내용 |
| --- | --- |
| session_id | 작업 세션 ID (수정요청 때 사용) |
| ad_copy | 광고 문구 |
| hashtags | 해시태그 목록 |
| original_image_url | 업로드한 원본 이미지 경로 |
| generated_image_url | AI 생성 이미지 경로 (생성 전이면 null) |
| elapsed_time | 소요 시간(초) |

### `POST /revise` (수정 재생성) — ⏳ 고도화 (이번 단계 제외)
요청: `session_id`, `revision_request`(수정 요청 텍스트)
응답: `/generate`와 동일 구조 (수정 반영된 새 결과)

## 7. DB 스키마 (MySQL)

### sessions
| 컬럼 | 의미 |
| --- | --- |
| session_id (PK) | 작업 단위 ID |
| created_at | 생성 시간 |

### messages
| 컬럼 | 의미 |
| --- | --- |
| message_id (PK) | 메시지 ID |
| session_id (FK) | 소속 세션 |
| role | user / assistant |
| content | 요청 또는 응답 내용 |
| created_at | 작성 시간 |

### generations
| 컬럼 | 의미 |
| --- | --- |
| generation_id (PK) | 생성 결과 ID |
| session_id (FK) | 소속 세션 |
| original_image_path | 업로드 원본 경로 |
| generated_image_path | 생성 이미지 경로 |
| ad_copy | 광고 문구 |
| prompt | 이미지 생성 프롬프트 |
| revision_request | 수정 요청 내용 (없으면 null) |
| created_at | 생성 시간 |

## 8. 이미지 생성 전략

- 텍스트(문구·프롬프트): **OpenAI API**
- 이미지 생성: **OpenAI Image API** (이번 단계). 셋업 부담이 적어 빠르게 동작 가능.
- **HuggingFace 모델 직접 서빙은 고도화로 미룸** (GPU 셋업·모델 선정 부담). 비용·품질 이슈 시 전환.
- `ml/image_gen.py`를 교체 가능한 인터페이스로 설계해, 나중에 HF로 갈아끼울 수 있게 한다.
- ⚠️ OpenAI Image API는 $30 한도를 빠르게 소모할 수 있으니, 테스트 시 호출 횟수에 주의.

## 9. 에러 처리
- 잘못된 파일 형식 / 필수 필드 누락 → 400 + 명확한 메시지
- OpenAI 호출 실패 / 한도 초과 → 502 + "잠시 후 재시도" (서버 안 죽게)
- DB 연결 실패 → 500 + 로그 기록

## 10. 기술 스택
| 영역 | 기술 |
| --- | --- |
| Backend | FastAPI (비동기), uv + requirements 병행 |
| Text | OpenAI API |
| Image | **OpenAI Image API** (HuggingFace는 고도화) |
| DB | **MySQL (Docker)** + SQLAlchemy |
| Frontend | **미정** (Streamlit 후보) |
| Infra | GCP VM(L4 GPU), .env 비밀관리 |

## 11. 확인/미정 항목
- [ ] **프론트엔드**: Streamlit vs 다른 것 (CORS 설정에 영향) — 팀 확인
- [ ] **MySQL 드라이버/방식**: 동기(pymysql) vs 비동기(asyncmy) — 구현 계획에서 결정
- [ ] OpenAI 모델 선택: 문구용 GPT-5.4 계열 / 이미지 GPT-image (한도 $30 내)
- [ ] (고도화) HuggingFace 이미지 모델 선정 — 이번 단계는 OpenAI Image API 사용

## 12. 구현 순서 (베이스라인)
1. `core/config.py` — 설정(.env: DB 접속정보, OPENAI_API_KEY)
2. `models/schemas.py` — 요청/응답 형태
3. `main.py` + `/health` — 서버 켜지는 것 확인
4. `docker-compose.yml` — MySQL 컨테이너 띄우기
5. `db/database.py` + `db/models.py` — 연결 + 테이블
6. `storage/files.py` — 업로드 저장
7. `ml/text_gen.py` — OpenAI 문구 생성
8. `api/endpoints.py` `/generate` + `services/pipeline.py` — 전체 조립 + DB 저장

## 13. 코딩 컨벤션
- 모든 함수에 **타입 힌트** 추가
- 함수 docstring = **한 줄 설명 + Args + Returns**
- 예:
```python
async def save_upload(image: UploadFile) -> Path:
    """업로드 사진을 저장하고 경로를 반환한다.

    Args:
        image: 업로드된 이미지 파일.
    Returns:
        저장된 파일의 경로.
    """
```
