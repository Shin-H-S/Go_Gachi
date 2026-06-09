# 생성 메타데이터 저장 확장 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 이미지 생성 1건에 사용된 사용자 문구와 로고 관련 메타데이터를 `generations` 테이블에 저장한다.

**Architecture:** 현재 생성 기록은 `generations`가 중심이고, `prompt_version`과 `model`은 이미 저장되고 있다. 이번 작업은 중복 컬럼을 만들지 않고 `user_copy`, `has_logo`, `logo_position`, `logo_image_hash`, `logo_storage_key`만 nullable/기본값 기반으로 추가한다. API 요청 스키마의 `userCopy`, `logoDataUrl`, `logoPosition` 추가 작업은 별도 담당자가 진행하므로, 해당 필드가 병합된 뒤 저장 연결을 맞춘다.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy ORM, Alembic, PostgreSQL/Supabase, pytest, ruff

---

## 현재 상태

- `generations.prompt_version`은 이미 있음.
- `generations.model`은 이미 있음.
- `prompt` 컬럼은 OpenAI에 실제로 보낸 최종 프롬프트 전체를 저장함.
- 사용자가 입력한 원문만 따로 저장하는 컬럼은 아직 없음.
- 로고 기능 코드는 아직 없고, API 요청 스키마에 `userCopy`, `logoDataUrl`, `logoPosition`을 추가하는 작업은 다른 담당자가 진행 예정.

## 이번 계획 범위

- `generations`에 생성 메타데이터 컬럼 추가
- 생성 기록 생성 시 메타데이터 저장
- 캐시 hit으로 `cached` 기록을 만들 때도 이번 요청의 메타데이터 저장
- `userCopy`가 생성 결과에 영향을 주는 사용자 프롬프트라면 `instruction_hash` 계산 입력에도 포함
- 테스트 추가

## 이번 계획에서 제외

- `parent_id` 기반 대화식 수정 이력
- 마이페이지 페이지네이션
- 원본 이미지 URL 방식
- API 응답에 메타데이터 노출
- 로고 이미지 합성 UI/파이프라인
- 로고 라이브러리용 별도 `logos` 테이블

---

### Task 1: DB 모델과 마이그레이션에 메타데이터 컬럼 추가

**Files:**
- Modify: `backend/app/db/models.py`
- Create via command: `migrations/versions/*_add_generation_metadata.py`

- [ ] **Step 1: `Generation` 모델에 컬럼 추가**

`backend/app/db/models.py`의 `Generation` 클래스에 아래 컬럼을 추가한다.

```python
user_copy: Mapped[str | None] = mapped_column(Text, nullable=True)
has_logo: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
logo_position: Mapped[str | None] = mapped_column(String(50), nullable=True)
logo_image_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
logo_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
```

- [ ] **Step 2: Alembic 마이그레이션 생성**

Alembic이 revision id를 자동 생성하도록 아래 명령으로 새 마이그레이션 파일을 만든다.

```powershell
uv run alembic revision -m "add generation metadata"
```

생성된 `migrations/versions/*_add_generation_metadata.py` 파일의 `upgrade()`에 아래 컬럼 추가를 작성한다.

```python
def upgrade() -> None:
    op.add_column("generations", sa.Column("user_copy", sa.Text(), nullable=True))
    op.add_column(
        "generations",
        sa.Column("has_logo", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column("generations", sa.Column("logo_position", sa.String(length=50), nullable=True))
    op.add_column("generations", sa.Column("logo_image_hash", sa.String(length=64), nullable=True))
    op.add_column("generations", sa.Column("logo_storage_key", sa.String(length=500), nullable=True))
```

`downgrade()`는 역순으로 제거한다.

```python
def downgrade() -> None:
    op.drop_column("generations", "logo_storage_key")
    op.drop_column("generations", "logo_image_hash")
    op.drop_column("generations", "logo_position")
    op.drop_column("generations", "has_logo")
    op.drop_column("generations", "user_copy")
```

- [ ] **Step 3: 마이그레이션 검증**

Run:

```powershell
uv run alembic upgrade head
```

Expected:

```text
마이그레이션 성공
Supabase/PostgreSQL의 generations 테이블에 새 컬럼 5개 추가
```

---

### Task 2: Generation 생성 함수에 메타데이터 인자 추가

**Files:**
- Modify: `backend/app/db/repositories/generations.py`
- No change expected: `backend/app/db/crud.py` already re-exports repository functions by name
- Test: `tests/db/test_crud_generation_cache.py`

- [ ] **Step 1: 실패 테스트 추가**

`tests/db/test_crud_generation_cache.py`에 아래 테스트를 추가한다.

```python
async def test_create_pending_generation_stores_generation_metadata(
    db_session: AsyncSession,
    tmp_dir: Path,
) -> None:
    generation = await crud.create_pending_generation(
        db_session,
        request_id="req-meta",
        image_hash="h-meta",
        preset_id="instagram",
        instruction_hash=crud.instruction_sha256("copy"),
        prompt_version="v1",
        model="gpt-image-2",
        original_path=str(tmp_dir / "input.png"),
        prompt="final prompt",
        user_copy="레몬에이드 신메뉴 광고 문구",
        has_logo=True,
        logo_position="bottom_right",
        logo_image_hash="a" * 64,
        logo_storage_key="logos/logo.png",
    )

    assert generation.user_copy == "레몬에이드 신메뉴 광고 문구"
    assert generation.has_logo is True
    assert generation.logo_position == "bottom_right"
    assert generation.logo_image_hash == "a" * 64
    assert generation.logo_storage_key == "logos/logo.png"
```

Run:

```powershell
uv run pytest tests/db/test_crud_generation_cache.py::test_create_pending_generation_stores_generation_metadata -q
```

Expected:

```text
FAIL: create_pending_generation() got an unexpected keyword argument
```

- [ ] **Step 2: `create_pending_generation` 인자 추가**

`backend/app/db/repositories/generations.py`의 `create_pending_generation`에 아래 인자를 추가한다.

```python
user_copy: str | None = None,
has_logo: bool = False,
logo_position: str | None = None,
logo_image_hash: str | None = None,
logo_storage_key: str | None = None,
```

`Generation(...)` 생성에도 같은 값을 넣는다.

```python
user_copy=user_copy,
has_logo=has_logo,
logo_position=logo_position,
logo_image_hash=logo_image_hash,
logo_storage_key=logo_storage_key,
```

- [ ] **Step 3: 테스트 통과 확인**

Run:

```powershell
uv run pytest tests/db/test_crud_generation_cache.py::test_create_pending_generation_stores_generation_metadata -q
```

Expected:

```text
PASS
```

---

### Task 3: 캐시 기록에도 메타데이터 복사

**Files:**
- Modify: `backend/app/db/repositories/generations.py`
- Test: `tests/db/test_crud_generation_cache.py`

- [ ] **Step 1: 실패 테스트 추가**

`tests/db/test_crud_generation_cache.py`에 아래 테스트를 추가한다.

```python
async def test_create_cached_generation_stores_generation_metadata(
    db_session: AsyncSession,
) -> None:
    cached = await crud.create_cached_generation(
        db_session,
        request_id="req-cached-meta",
        image_hash="h-meta",
        preset_id="instagram",
        instruction_hash=crud.instruction_sha256("copy"),
        prompt_version="v1",
        model="gpt-image-2",
        original_path="uploads/input.png",
        output_path="outputs/result.png",
        image_url=None,
        prompt="final prompt",
        user_copy="레몬에이드 신메뉴 광고 문구",
        has_logo=True,
        logo_position="bottom_right",
        logo_image_hash="b" * 64,
        logo_storage_key="logos/logo.png",
    )

    assert cached.status == "cached"
    assert cached.user_copy == "레몬에이드 신메뉴 광고 문구"
    assert cached.has_logo is True
    assert cached.logo_position == "bottom_right"
    assert cached.logo_image_hash == "b" * 64
    assert cached.logo_storage_key == "logos/logo.png"
```

Run:

```powershell
uv run pytest tests/db/test_crud_generation_cache.py::test_create_cached_generation_stores_generation_metadata -q
```

Expected:

```text
FAIL: create_cached_generation() got an unexpected keyword argument
```

- [ ] **Step 2: `create_cached_generation` 인자 추가**

`backend/app/db/repositories/generations.py`의 `create_cached_generation`에 아래 인자를 추가한다.

```python
user_copy: str | None = None,
has_logo: bool = False,
logo_position: str | None = None,
logo_image_hash: str | None = None,
logo_storage_key: str | None = None,
```

`Generation(...)` 생성에도 같은 값을 넣는다.

```python
user_copy=user_copy,
has_logo=has_logo,
logo_position=logo_position,
logo_image_hash=logo_image_hash,
logo_storage_key=logo_storage_key,
```

- [ ] **Step 3: 테스트 통과 확인**

Run:

```powershell
uv run pytest tests/db/test_crud_generation_cache.py::test_create_cached_generation_stores_generation_metadata -q
```

Expected:

```text
PASS
```

---

### Task 4: 생성 파이프라인에서 userCopy/logo 메타데이터 저장 연결

**Files:**
- Modify: `backend/app/schemas.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/services/generation_service.py`
- Test: `tests/api/test_generate_cache.py`

> 이 Task는 API 요청 스키마 담당자의 `userCopy`, `logoDataUrl`, `logoPosition` 변경이 병합된 뒤 진행한다. 아직 병합 전이면 이 Task는 대기한다.

- [ ] **Step 1: 스키마 필드 확인**

`backend/app/schemas.py`의 `GenerateRequest`에 아래 필드가 있는지 확인한다.

```python
user_copy: str | None = Field(default=None, alias="userCopy")
logo_data_url: str | None = Field(default=None, alias="logoDataUrl")
logo_position: str | None = Field(default="bottom_right", alias="logoPosition")
```

- [ ] **Step 2: `edit_image` 인자 추가**

`backend/app/services/generation_service.py`의 `edit_image`에 아래 인자를 추가한다.

```python
user_copy: str | None = None,
logo_data_url: str | None = None,
logo_position: str | None = None,
```

로고 저장 로직이 아직 없으면 아래처럼 메타데이터만 저장한다.

```python
clean_user_copy = user_copy.strip() if user_copy else None
has_logo = bool(logo_data_url)
logo_image_hash = None
logo_storage_key = None
```

- [ ] **Step 3: userCopy를 생성 입력과 캐시 키에 반영**

`userCopy`가 사용자 프롬프트라면 생성 결과에 영향을 주는 값이다. 따라서 저장만 하고 캐시 키에서 빼면, 문구만 다른 요청이 기존 캐시를 잘못 재사용할 수 있다. `feedback_with_context(...)`를 호출하기 전에 아래처럼 최종 생성 입력에 포함한다.

```python
feedback_parts = [feedback]
if clean_user_copy:
    feedback_parts.append(f"User copy: {clean_user_copy}")
feedback_for_generation = "\n".join(part.strip() for part in feedback_parts if part.strip())
```

기존 코드의 `feedback_with_context(feedback, ...)` 호출은 아래처럼 바꾼다.

```python
generation_feedback = feedback_with_context(
    feedback_for_generation,
    target_size,
    selected_detail,
    resize_mode,
)
```

이렇게 해야 `instruction_hash = crud.instruction_sha256(generation_feedback)`에도 `userCopy`가 포함된다.

- [ ] **Step 4: pending 저장에 메타데이터 전달**

`crud.create_pending_generation(...)` 호출에 아래 값을 추가한다.

```python
user_copy=clean_user_copy,
has_logo=has_logo,
logo_position=logo_position if has_logo else None,
logo_image_hash=logo_image_hash,
logo_storage_key=logo_storage_key,
```

- [ ] **Step 5: cached 저장에 이번 요청 메타데이터 전달**

`cached` 행은 "이번 요청은 캐시를 사용했다"는 기록이다. 따라서 메타데이터는 원본 success 행의 값을 무조건 복사하지 않고, 이번 요청에서 받은 값을 저장한다.

```python
user_copy=clean_user_copy,
has_logo=has_logo,
logo_position=logo_position if has_logo else None,
logo_image_hash=logo_image_hash,
logo_storage_key=logo_storage_key,
```

만약 구현 중 `cached_snapshot`에 `has_logo` 같은 bool 값을 포함한다면 타입 힌트도 같이 넓힌다.

```python
cached_snapshot: dict[str, object] | None
```

- [ ] **Step 6: main에서 request 값을 service로 전달**

`backend/app/main.py`의 `edit_image(...)` 호출에 아래 값을 추가한다.

```python
user_copy=request.user_copy,
logo_data_url=request.logo_data_url,
logo_position=request.logo_position,
```

- [ ] **Step 7: API 저장 테스트 추가**

`tests/api/test_generate_cache.py`에 아래 테스트를 추가한다.

```python
def test_generate_stores_user_copy_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_call(**kwargs):  # noqa: ANN003, ANN202
        return TINY_PNG_B64

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "detailType": "square_feed",
            "feedback": "밝게",
            "userCopy": "레몬에이드 신메뉴 광고 문구",
        },
    )

    assert response.status_code == 200

    async def _saved_copy() -> str | None:
        async with async_session_scope() as db:
            result = await db.execute(select(Generation.user_copy))
            return result.scalar_one()

    assert asyncio.run(_saved_copy()) == "레몬에이드 신메뉴 광고 문구"
```

Run:

```powershell
uv run pytest tests/api/test_generate_cache.py::test_generate_stores_user_copy_metadata -q
```

Expected:

```text
PASS
```

---

### Task 5: 최종 검증

**Files:**
- All modified files

- [ ] **Step 1: DB 테스트 실행**

Run:

```powershell
uv run pytest tests/db -q
```

Expected:

```text
PASS
```

- [ ] **Step 2: 생성 API 테스트 실행**

Run:

```powershell
uv run pytest tests/api/test_generate_cache.py tests/api/test_generate_validation.py -q
```

Expected:

```text
PASS
```

- [ ] **Step 3: 전체 테스트 실행**

Run:

```powershell
uv run pytest -q
```

Expected:

```text
PASS
```

- [ ] **Step 4: 린트 실행**

Run:

```powershell
uv run ruff check .
```

Expected:

```text
All checks passed!
```

---

## 팀 공유 메모

- `prompt_version`, `model`은 이미 있으므로 새로 추가하지 않는다.
- `prompt`는 최종 프롬프트 전체이고, `user_copy`는 사용자가 직접 입력한 문구만 저장한다.
- `userCopy`는 사용자 프롬프트로 보고, 생성 입력과 `instruction_hash` 계산에도 포함한다.
- 캐시 키는 기존 구조(`image_hash + preset_id + instruction_hash + model + prompt_version`)를 유지한다. 대신 `instruction_hash` 안에 `userCopy`가 반영되도록 한다.
- 캐시 hit으로 `cached` 행을 만들 때 `user_copy`와 로고 메타데이터는 이번 요청 값을 저장한다.
- `logoDataUrl` 원문 base64는 DB에 저장하지 않는다.
- 이번 PR에서는 로고 파일 자체를 저장하지 않는다. 로고 파이프라인(R2/GCS/로컬 저장)이 들어오면 `logo_image_hash`, `logo_storage_key`를 실제 값으로 채운다.
- 지금 단계에서는 로고 기능이 없어도 `has_logo=false`, 로고 관련 컬럼 `null`로 안전하게 동작해야 한다.
- 이번 PR은 DB 저장까지가 범위다. `/api/generate` 응답이나 `/api/auth/me/generations` 응답에 메타데이터를 노출하는 작업은 후속 PR로 분리한다.
- 마이그레이션은 dev Supabase에서 먼저 적용·검증한 뒤 prod에 적용한다. prod 적용 전에는 백업 여부를 확인한다.
