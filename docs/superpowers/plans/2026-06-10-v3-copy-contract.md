# V3 Copy Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the Streamlit frontend to send `userPrompt`, `userCopy`, `copyMode`, and `textOverlayEnabled` separately and show backend `copy` output.

**Architecture:** Keep API contract changes inside `frontend/services/api_client.py`, keep work-page generation state inside `frontend/work/*`, and keep page composition in `frontend/pages/work.py`. Preserve the existing backend schema and logo fields.

**Tech Stack:** Python 3.11, Streamlit, pytest, FastAPI backend contract.

---

### Task 1: Update API Contract Tests

**Files:**
- Modify: `tests/frontend/test_api_client_generation.py`

- [ ] **Step 1: Write failing tests**
  - Change the expected payload so `userPrompt` contains only image direction context.
  - Assert `userCopy` is sent separately.
  - Assert backend `copy` metadata can be returned from `request_backend`.

- [ ] **Step 2: Run tests and verify failure**
  - Run: `uv run pytest tests/frontend/test_api_client_generation.py -q`
  - Expected: failures around missing `userCopy` and response metadata.

### Task 2: Implement API Boundary

**Files:**
- Modify: `frontend/services/api_client.py`

- [ ] **Step 1: Implement minimal contract change**
  - Add a small generation result return object.
  - Send `userCopy` as the trimmed ad copy field.
  - Keep `userPrompt` for image generation direction only.
  - Preserve `copyMode`, `textOverlayEnabled`, and logo fields.

- [ ] **Step 2: Run API client tests**
  - Run: `uv run pytest tests/frontend/test_api_client_generation.py -q`
  - Expected: pass.

### Task 3: Update Copy Controls and Work State

**Files:**
- Modify: `tests/frontend/test_text_overlay_ui.py`
- Modify: `tests/frontend/test_ad_copy.py`
- Modify: `tests/test_frontend_routing_state.py`
- Modify: `frontend/work/copy_controls.py`
- Modify: `frontend/work/copy.py`
- Modify: `frontend/work/state.py`

- [ ] **Step 1: Write failing UI/state tests**
  - Assert copy-mode labels are rendered.
  - Assert default copy mode is `preserve`.
  - Assert result context tracks copy mode.

- [ ] **Step 2: Implement controls**
  - Replace automatic mode selection with user-selectable mode labels:
    `그대로 사용`, `자연스럽게 다듬기`, `홍보 문구로 바꾸기`.
  - Keep `preserve` as default.

- [ ] **Step 3: Run focused tests**
  - Run: `uv run pytest tests/frontend/test_text_overlay_ui.py tests/frontend/test_ad_copy.py tests/test_frontend_routing_state.py -q`
  - Expected: pass.

### Task 4: Store and Display Backend Copy Output

**Files:**
- Modify: `frontend/work/generation.py`
- Modify: `frontend/pages/work.py`
- Optionally create: `frontend/work/result_copy.py`
- Test: `tests/frontend/test_text_overlay_ui.py`

- [ ] **Step 1: Write failing test**
  - Assert the work page renders a backend copy/result-copy helper area.

- [ ] **Step 2: Implement storage and rendering**
  - Store `result_copy` in `st.session_state`.
  - Clear it when result state is stale.
  - Show copy fields under the generated result when present.

- [ ] **Step 3: Run focused tests**
  - Run: `uv run pytest tests/frontend/test_text_overlay_ui.py tests/test_frontend_routing_state.py -q`
  - Expected: pass.

### Task 5: Document Contract for Future Agents

**Files:**
- Modify: `frontend/AGENTS.md`

- [ ] **Step 1: Add V3 copy contract note**
  - Document that frontend must not use legacy `feedback`.
  - Document request fields and copy-mode labels.
  - Document that response `copy` should be displayed when present.

- [ ] **Step 2: Run frontend test suite**
  - Run: `uv run pytest tests/frontend tests/test_frontend_routing_state.py -q`
  - Expected: pass.
