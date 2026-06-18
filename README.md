<div align="center">

# ☕ Go Gachi 🐾

🌸 소상공인을 위한 AI 광고 이미지 자동 생성 서비스
📸 메뉴 사진 한 장으로 인스타그램·배민·당근마켓 광고 이미지를 만들어드립니다.

<img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11" />
<img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
<img src="https://img.shields.io/badge/Streamlit-Frontend-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit" />
<img src="https://img.shields.io/badge/Supabase-Auth%20%2B%20DB-3FCF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase" />
<img src="https://img.shields.io/badge/Cloudflare-R2-F38020?style=for-the-badge&logo=cloudflare&logoColor=white" alt="Cloudflare R2" />
<img src="https://img.shields.io/badge/OpenAI-GPT--image--2-412991?style=for-the-badge&logo=openai&logoColor=white" alt="OpenAI" />

🔗 **[Live Demo](https://gogachi.streamlit.app)**

</div>

> ## 🔗 Project Links

| 항목 | 링크 |
| --- | --- |
| PPT |  |
| 보고서 | [Go Gachi 최종 보고서 PDF](docs/Go_Gachi-final-report.pdf) |
| 협업 일지 | [Notion](https://www.notion.so/b097f345c16a82e58dff01887960931e?source=copy_link) |

---

> ## ☕ 프로젝트 소개

### 1. 프로젝트 배경

디지털 마케팅의 중요성이 커지면서 소상공인들의 광고 이미지 제작 수요도 꾸준히 늘고 있습니다.
<br>그러나 소상공인 다수는 전문 디자인 도구 활용에 어려움을 겪고, 외주 제작에 시간과 비용 부담을 안고 있습니다.
<br>특히 **인스타그램·배달앱·지역 커뮤니티(당근마켓)** 등 채널마다 요구하는 이미지 규격과 시각적 표현 방식이 달라, <br>같은 메뉴 사진을 매번 반복 제작해야 하는 비효율이 발생합니다.

### 2. 서비스 정의

**Go Gachi**는 소상공인이 보유한 원본 메뉴 사진 한 장을 업로드하면, <br>광고 채널과 상세 규격에 맞춰 최적화된 광고 이미지를 자동으로 생성하는 **AI 기반 광고 제작 솔루션**입니다.
<br>디지털 도구에 익숙하지 않은 사용자도 쉽게 사용할 수 있도록 **업종 → 채널 → 유형 → 요청사항·문구 옵션** 순서의 직관적인 워크플로우를 제공합니다.

📌 **현재 MVP 타깃 업종**: 카페

📌 **지원 채널**: 인스타그램, 배달의민족, 당근마켓

### 3. 타깃 사용자

- 인스타그램·배달앱·당근마켓에 광고를 올리는 소상공인
- 디자인 도구에 익숙하지 않은 운영자
- 짧은 시간 안에 광고 이미지가 필요한 사용자

---

> ## 🎯 MVP 목표 및 핵심 기능

- **매체별 규격 대응**
<br>인스타그램(정사각/세로형/스토리), 배달의민족(단색/공간 배경), 당근마켓(메뉴/할인 이벤트) 총 **3개 채널 7가지 레이아웃 규격** 자동 보정.
- **상품성 보존**
<br>사용자가 업로드한 원본 상품의 형태, 색상, 질감을 왜곡 없이 유지.

- **비동기 생성 구조 구축**
<br>이미지 생성 모델의 긴 추론 시간(Latency) 동안 UI가 멈추지 않도록 **비동기 Job 시스템** 도입.

- **3대 문구 모드 지원**
<br>입력 문구 그대로 사용(Preserve), 자연스럽게 다듬기(Polish), 홍보 문구로 변환(Rewrite) 기능 제공 및 미입력 시 자동 생성.

---

> ## ✨ 핵심 기능

| 기능 | 설명 |
| --- | --- |
| 🖼️ **AI 광고 이미지 생성** | 원본 사진 + 채널/유형/요청사항 → AI가 광고 이미지를 자동 생성 |
| ✍️ **광고 문구 자동 생성** | 채널과 업종에 맞는 광고 문구를 함께 제안 |
| 📐 **채널별 규격 자동 최적화** | 인스타그램·배민·당근의 권장 사이즈로 자동 리사이즈 |
| 📁 **마이페이지** | 생성 기록 관리, 폴더 분류, 페이지 단위 조회 |
| ⬇️ **1-Click 다운로드** | signed URL 기반 즉시 다운로드 (마이페이지·생성 페이지) |
| 🎨 **생성 대기 애니메이션** | 60~90초 생성 시간 동안 커스텀 로딩 아이콘 + 촬영 팁 로테이션으로 체감 대기 시간 단축 |
| 🚪 **무료 시작 / 로그인 모드** | 비로그인은 즉시 사용, 로그인은 작업 기록 보관 |

---

> ## 🍰 서비스 흐름

```
[1] 사진 업로드  →  [2] 채널·유형 선택  →  [3] 요청사항·문구 입력
                                                  ↓
[6] 다운로드  ←  [5] 결과 미리보기  ←  [4] AI가 이미지 + 문구 생성
```

1. 사용자가 원본 메뉴 사진을 업로드합니다.
2. 광고 채널(인스타그램·배민·당근)과 유형(피드/스토리/할인/이벤트 등)을 선택합니다.
3. 이미지 요청사항과 광고 문구 옵션을 입력합니다.
4. 백엔드가 비동기 Job으로 OpenAI에 이미지·문구 생성을 요청합니다.
5. 생성이 완료되면 결과 이미지와 문구를 미리보기로 보여줍니다.
6. 다운로드 버튼 한 번으로 결과 이미지를 받습니다 (로그인 사용자는 마이페이지에 자동 보관).

---

> ## 🏠 시스템 아키텍처

```
사용자 (브라우저)
    ↓
Streamlit Cloud (프론트엔드)
    ↓ HTTPS
Render (FastAPI 백엔드)
    ├→ Supabase (Auth + PostgreSQL)
    ├→ Cloudflare R2 (이미지 저장 + signed URL)
    └→ OpenAI API (이미지·문구 생성)
```

- **Streamlit Cloud**: 프론트엔드 호스팅. 사용자 브라우저와 WebSocket으로 통신.
- **Render**: FastAPI 백엔드 컨테이너 호스팅. 시작 시 Alembic 마이그레이션 자동 적용.
- **Supabase**: 사용자 인증(JWT)과 PostgreSQL 데이터 저장.
- **Cloudflare R2**: 업로드 원본 이미지와 생성 결과 이미지 저장. 다운로드는 short-lived signed URL로 발급.
- **OpenAI API**: 이미지 생성(`gpt-image-2`)과 광고 문구 생성(`gpt-5.4-mini`) 호출.

---

> ## 🛠️ 기술 스택

| 영역 | 사용 기술 |
| --- | --- |
| 프론트엔드 | Streamlit, Python 3.11 |
| 백엔드 | FastAPI, Python 3.11, uv |
| 인증·DB | Supabase (Auth + PostgreSQL) |
| 이미지 저장 | Cloudflare R2 (S3 호환, signed URL) |
| AI | OpenAI `gpt-image-2`, `gpt-5.4-mini` |
| DB 마이그레이션 | Alembic |
| 테스트·린팅 | pytest, ruff |
| 배포 | Render (백엔드), Streamlit Community Cloud (프론트) |
| CI | GitHub Actions |

---

> ## 📁 프로젝트 구조

```
Go_Gachi/
├── backend/                    # FastAPI 백엔드
│   └── app/
│       ├── api/                # 라우트 (auth, mypage, assets, generation_jobs 등)
│       ├── core/               # 설정, 인증, 로깅, 에러 변환
│       ├── db/                 # SQLAlchemy 모델 + 레포지토리
│       └── services/           # 이미지 생성, R2 스토리지, OpenAI 연동
├── frontend/                   # Streamlit 프론트엔드
│   ├── pages/                  # 작업 페이지, 마이페이지 진입점
│   ├── work/                   # 생성 페이지 컴포넌트·상태
│   ├── mypage/                 # 마이페이지 컴포넌트·캐시·데이터 로더
│   ├── services/               # 백엔드 API 클라이언트
│   └── core/                   # 라우터, 환경 설정
├── config/                     # 광고 채널·규격 프리셋 JSON
├── migrations/                 # Alembic 마이그레이션 스크립트
├── tests/                      # 백엔드·프론트엔드 테스트
├── docs/                       # 아키텍처·개발·배포 문서
├── infra/
│   └── Dockerfile              # 백엔드 Docker 이미지
├── scripts/                    # 개발용 유틸리티 스크립트
├── .streamlit/                 # Streamlit 설정 (toolbarMode 등)
└── render.yaml                 # Render 배포 Blueprint
```

---

> ## 💡 주요 기술적 결정

### 1. 프롬프트·생성 정책

| 결정 | 핵심 이유 |
| --- | --- |
| **채널별 시스템 프롬프트 분리** (Instagram·배민·당근) | 채널마다 요구하는 레이아웃·톤·텍스트 정책이 달라 단일 프롬프트로 통합 불가 |
| **광고 문구 렌더링 모드 분기** | Instagram은 텍스트 포함, 배민은 텍스트 금지(썸네일 정책), 당근은 할인 이벤트만 렌더 — 채널 운영 규칙 반영 |
| **상품성 보존 정책 강화** | 음료 내용물·토핑·재료를 변형하지 않도록 prompt에 명시 → 이미지 모델의 임의 변형 차단 |
| **3대 문구 모드 (Preserve / Polish / Rewrite)** | 사용자가 직접 입력한 문구의 다양한 활용 방식 지원 + 미입력 시 자동 생성 |
| **`PROMPT_VERSION` 코드 상수화** | 프롬프트 변경 시 캐시 무효화를 코드 커밋 단위로 관리, 운영 환경 어긋남 방지 |

### 2. 백엔드 아키텍처

| 결정 | 핵심 이유 |
| --- | --- |
| **비동기 Job 방식 이미지 생성** | OpenAI 이미지 모델 추론에 60~90초 소요 → UI 멈춤 방지를 위해 즉시 `request_id` 반환 + polling 구조 |
| **Cloudflare R2 외부 스토리지** | Render 컨테이너 디스크는 휘발성, 재배포 시 파일 유실 → R2 분리로 안정성 확보 |
| **Supabase Auth + JWKS 검증** | ES256/RS256/HS256 동시 지원 + 1시간 단위 키 캐시 → Supabase 키 회전 대응 |
| **사용자별 데이터 격리** (`user_id` 기준 조회) | 본인 데이터만 접근 가능하도록 모든 마이페이지 라우트에서 `user_id` 필터 적용 |
| **컨테이너 시작 시 Alembic 자동 마이그레이션** | 배포 후 마이그레이션 수동 실행 누락 위험 차단 |
| **비용을 이미지·텍스트로 분리 저장** (`image_cost_usd` / `text_cost_usd`) | 모델별 단가 차이를 운영 단계에서 분석 가능하도록 분리 기록 |

### 3. 프론트엔드·UX

| 결정 | 핵심 이유 |
| --- | --- |
| **생성 진행 알림 + 결과 미리보기** | 60~90초 대기 시간 동안 진행 상황을 시각적으로 전달해 체감 대기 시간 단축 |
| **커스텀 로딩 애니메이션 + 촬영 팁 로테이션** | 단순 스피너 대신 12종 파스텔 배경 + SVG 아이콘 + 7초 간격 촬영 팁(8개 이상)을 순환 노출해 대기 경험을 콘텐츠로 전환 |
| **`st.fragment` 기반 폴링** | Streamlit 전체 rerun 없이 3초마다 생성 상태만 갱신, 다른 UI 상태 보존 |
| **응답 페이로드 경량화** (`/me/uploads` base64 제거) | 업로드 이미지 base64 인라인 → URL 참조로 전환, 응답 크기 최대 약 98% 감소 |
| **마이페이지 페이지네이션 + 캐싱** | 백엔드 페이지 단위 호출 + `st.cache_data` + mutation invalidation → 첫 진입과 인터랙션 모두 빠르게 |
| **signed URL 1-Click 다운로드** | R2 short-lived signed URL을 응답에 박아 보안(TTL 30분) + 1-click UX 동시 만족 |

---

> ## 🌱 시작하기 (로컬 실행)

### 1. 사전 준비
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) 설치

### 2. 설치

```bash
git clone https://github.com/Shin-H-S/Go_Gachi.git
cd Go_Gachi
uv sync
```

### 3. 환경 변수 설정

레포 최상단에 `.env` 파일을 만들고 필요한 환경 변수를 채워넣습니다. 운영 환경에서는 Render와 Streamlit Cloud의 환경변수 UI에서 직접 주입합니다.

> ⚠️ `.env`는 절대 커밋하지 마세요.

### 4. 실행

**터미널 1 — 백엔드**

```bash
uv run uvicorn backend.app.main:app --reload
```

**터미널 2 — 프론트엔드**

```bash
uv run streamlit run frontend/app.py
```

브라우저에서 http://localhost:8501 로 접속합니다.

---

> ## 🧪 테스트와 린팅

### 1. 전체 테스트

```bash
uv run pytest
```

### 2. 린트와 포맷

```bash
uv run ruff check
uv run ruff format
```

CI(GitHub Actions)에서도 동일하게 `ruff check`와 `pytest`를 실행합니다.

---

> ## ☁️ 배포

| 환경 | 호스팅 | URL |
| --- | --- | --- |
| 프론트엔드 | Streamlit Community Cloud | <https://gogachi.streamlit.app> |
| 백엔드 | Render (FastAPI on Docker) | (내부 운영 URL) |

- **백엔드**: [`render.yaml`](render.yaml) 기반 Render Blueprint로 자동 배포됩니다.
  컨테이너 시작 시 [`infra/Dockerfile`](infra/Dockerfile)의 CMD가 `alembic upgrade head`를 먼저 실행해 운영 DB 스키마를 항상 최신 상태로 유지합니다.
- **프론트엔드**: Streamlit Community Cloud가 `frontend/app.py`를 자동 빌드·배포합니다.

---

> ## 🚧 한계점 & 향후 고도화

### 1. 도메인·UX 한계와 개선 방향

- **도메인 환각(Hallucination) 리스크 관리**
<br>이미지 모델이 텍스트를 렌더링할 때 철자 오류가 나거나, 플랫폼 특성을 과해석하여 음료명을 잘못 기재(예: 당근 주스 오작명)하는 이슈가 관찰됨. 향후 시스템 프롬프트 제어력(Negative Prompting)을 고도화할 계획.

- **이미지 품질 의존성 극복**
<br>저품질 원본에 대한 품질 저하 현상을 막기 위해, 프론트엔드 내 '업로드 이미지 촬영 가이드' 제공을 강화.

- **UX 및 아키텍처 고도화**
<br>동기식 `/api/generate` 흐름을 완전히 폐기(Deprecated)하고 비동기 Job 단일 구조로 고도화. 문구 생성과 이미지 합성을 UI에서 분리하여 체감 대기 시간을 개선할 예정.

### 2. 운영·인프라 한계

| 영역 | 한계 |
| --- | --- |
| **콜드스타트** | Render Free tier가 5분 idle 후 sleep → 첫 요청에 5~30초 소요 |
| **Cross-region latency** | Streamlit Cloud(미국) ↔ Render(싱가포르) ↔ Supabase 사이 네트워크 hop이 누적 |
| **OpenAI 비용 제어** | 사용자별·시간별 rate limit 미적용으로 비용 폭주 가능성 |
| **모바일 UX** | Streamlit 구조상 모바일 최적화 한계 |
| **MVP 업종 제한** | 현재 카페만 지원, 다른 업종 프리셋 미구현 |
| **미분류 폴더 백엔드 페이지네이션 부재** | `folder_id IS NULL` 필터 미지원으로 전체 로드 fallback |
| **다국어 미지원** | 한국어 단일 언어 |

### 3. 향후 고도화 방향

| 영역 | 방향 |
| --- | --- |
| **인프라** | UptimeRobot ping으로 콜드스타트 임시 해소, 본격 운영 시 Render Starter 또는 도쿄 리전(Fly.io 등)으로 이전 |
| **비용 관리** | OpenAI 라우트에 사용자별 rate limit + 일일 사용 한도 도입 (slowapi) |
| **업종 확장** | 음식점·미용실·학원 등 업종 프리셋 추가, 채널·유형 매트릭스 일반화 |
| **모바일 전용 UI** | React Native 또는 PWA로 모바일 친화 UI 제공 |
| **이미지 편집 기능** | 생성 후 부분 수정·재생성·문구 변경 인터랙션 추가 |
| **A/B 테스트** | 같은 입력으로 여러 변형 생성 후 사용자 선택 데이터 수집 |
| **분석 대시보드** | 사용자별 생성 비용·횟수·채널 분포 시각화 |
| **다국어** | i18n 도입 (한국어 → 영어, 일본어 확장) |
| **미분류 폴더 페이지네이션** | 백엔드 `folder_id IS NULL` 필터 추가 |

---

> ## 🐾 Team & Contributions


<table>
<thead>
<tr>
  <th align="center">파트</th>
  <th align="center">담당자</th>
  <th align="center">책임 영역</th>
</tr>
</thead>
<tbody>

<tr>
<td align="center"><b>PM</b></td>
<td align="center">
  <img src="docs/assets/흰%20냥이.png" alt="이건호" width="100" /><br>
  <b>이건호</b>
</td>
<td>

- 프로젝트 매니징, 회의록, 협업일지 가이드
- 일정 관리, 보고서 총괄
- 발표 자료 통합

</td>
</tr>

<tr>
<td align="center"><b>FE</b><br>(프론트엔드)</td>
<td align="center">
  <img src="docs/assets/회색%20냥이.png" alt="손승만" width="100" /><br>
  <b>손승만</b>
</td>
<td>

- Streamlit UI 전체, 사용자 흐름
- 카테고리 버튼, 결과물 표시
- 휴먼인루프 UI

</td>
</tr>

<tr>
<td align="center"><b>BE</b><br>(백엔드)</td>
<td align="center">
  <img src="docs/assets/크림%20냥이.png" alt="김예주" width="100" /><br>
  <b>김예주</b>
</td>
<td>

- API 라우팅
- 이미지 업로드 처리
- DB, 캐싱
- 배포 (Render, Streamlit Cloud, Cloudflare R2)

</td>
</tr>

<tr>
<td align="center"><b>BE + 팀장</b></td>
<td align="center">
  <img src="docs/assets/검은%20냥이.png" alt="신현수" width="100" /><br>
  <b>신현수</b>
</td>
<td>

- 생성 파이프라인 구축, 응답 속도 최적화
- OpenAI API 연동, 모델 서빙
- GCP 인프라
- PM 보조

</td>
</tr>

<tr>
<td align="center"><b>PE</b><br>(프롬프트 엔지니어)</td>
<td align="center">
  <img src="docs/assets/삼색%20냥이.png" alt="이수민" width="100" /><br>
  <b>이수민</b>
</td>
<td>

- 프롬프트 엔지니어링, 업종별 템플릿
- 결과물 자연스러움 튜닝
- 모델 성능 평가

</td>
</tr>

</tbody>
</table>
