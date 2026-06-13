"""New-test tab UI for the experiments Streamlit console."""

import json
import time

import streamlit as st
from app_common import RUNS_DIR
from app_generation import _to_data_url, start_run
from app_prompting import (
    API_SIZES,
    COPY_MODE_OPTIONS,
    DIRECT,
    REPO_DEFAULT,
    assemble_full_prompt,
    preview_ad_copy,
)
from app_state import list_runs, widget_state_from_cfg
from runner import load_settings

from backend.app.core.presets import get_presets
from backend.app.services.costs import calculate_image_cost


def render_new_tab() -> None:
    if "_flash" in st.session_state:
        st.success(st.session_state.pop("_flash"))

    presets = get_presets()

    name = st.text_input("테스트명", key="test_name")

    with st.expander("설정 불러오기 — 이전 테스트의 설정값 재사용"):
        config_runs = list_runs("config.json")
        if not config_runs:
            st.caption("저장된 이전 테스트가 없습니다.")
        else:
            labels = {}
            for run_id, run_dir in config_runs:
                try:
                    saved = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
                except ValueError:
                    continue
                labels[f"{saved.get('name', run_id)}  ·  {run_id[:15]}"] = saved
            selected_label = st.selectbox("이전 테스트", list(labels.keys()), key="load_select")
            chosen = labels.get(selected_label)
            if chosen:
                st.caption(
                    f"채널 {chosen.get('channel_label')} / 유형 {chosen.get('detail_label')} / "
                    f"문구 {'O' if chosen.get('copy_on') else 'X'} / "
                    f"{chosen.get('count')}장 · {chosen.get('quality')}"
                )
                if st.button("이 설정 불러오기"):
                    st.session_state["_pending_load"] = widget_state_from_cfg(chosen)
                    st.session_state["_flash"] = (
                        f"'{chosen.get('name')}' 설정을 불러왔습니다. "
                        "이미지 파일은 다시 업로드해주세요."
                    )
                    st.rerun()

    st.subheader("① 입력 이미지")
    image_file = st.file_uploader(
        "메뉴 사진 (1장, 필수)", type=["png", "jpg", "jpeg", "webp"], key="menu_image"
    )
    if image_file:
        st.image(image_file, width=180)

    st.subheader("② 광고 채널 · 유형")
    channel_labels = [p.label for p in presets.values()] + [DIRECT]
    channel_label = st.radio("광고 채널", channel_labels, horizontal=True, key="channel")
    channel_custom = ""
    if channel_label == DIRECT:
        channel_custom = st.text_area(
            "채널 프롬프트 직접입력 (채널 스타일/레이아웃 규칙을 영어로)",
            key="channel_custom",
            height=120,
            placeholder="예: Use the uploaded product image as the only main subject. ...",
        )
        preset = None
    else:
        preset = next(p for p in presets.values() if p.label == channel_label)

    detail_labels = ([d.label for d in preset.details] if preset else []) + [DIRECT]
    detail_label = st.radio(
        "광고 유형", detail_labels, horizontal=True, key=f"detail_{channel_label}"
    )
    detail_custom = ""
    detail = (
        preset.find_detail(
            next((d.id for d in preset.details if d.label == detail_label), None)
        )
        if preset
        else None
    )
    if detail_label == DIRECT:
        detail_custom = st.text_area(
            "유형 프롬프트 직접입력 (구도/배치 규칙)",
            key=f"detail_custom_{channel_label}",
            height=100,
            placeholder="예: Compose for a 1:1 feed layout. Place the product at the center. ...",
        )
        size_label = st.selectbox("출력 규격", [s[0] for s in API_SIZES], key="api_size")
        size = next(s for s in API_SIZES if s[0] == size_label)
        api_size, target_w, target_h = size[1], size[2], size[3]
    else:
        api_size, target_w, target_h = detail.api_size, detail.width, detail.height
        st.caption(f"규격: {detail.width}x{detail.height} (API {detail.api_size})")

    st.subheader("③ 광고 문구")
    copy_on = st.checkbox("문구 적용", key="copy_on")
    copy_text, copy_mode, copy_mode_custom, copy_instr_custom = "", "preserve", "", ""
    if copy_on:
        copy_text = st.text_area(
            "문구 입력",
            key="copy_text",
            height=90,
            placeholder="예: 가을 신메뉴 고구마 라떼 4,900원 (빈칸이면 AI가 자동 생성)",
            help=(
                "'그대로 사용'은 입력 전체가 헤드라인 한 줄로 들어갑니다. "
                "'다듬기/바꾸기'는 AI가 헤드라인·서브카피·CTA로 구성합니다. "
                "빈칸으로 두면 서비스와 동일하게 채널·유형·유저 프롬프트 맥락으로 "
                "AI가 문구를 자동 생성합니다 ('직접입력' 모드만 예외로 기본 문구 사용)."
            ),
        )
        mode_label = st.radio(
            "문구 옵션",
            [label for label, _ in COPY_MODE_OPTIONS],
            horizontal=True,
            key="copy_mode",
        )
        copy_mode = next(mode for label, mode in COPY_MODE_OPTIONS if label == mode_label)
        if copy_mode == "custom":
            copy_mode_custom = st.text_area(
                "문구 처리 지시 직접입력 (입력 문구는 그대로 렌더되고, 이 지시문이 추가됨)",
                key="copy_mode_custom",
                height=80,
                placeholder="예: Render the headline in a bold retro Korean font style. ...",
            )
        copy_source = st.radio(
            "문구 렌더링 프롬프트", [REPO_DEFAULT, DIRECT], horizontal=True, key="copy_source"
        )
        if copy_source == DIRECT:
            copy_instr_custom = st.text_area(
                "문구 렌더링 프롬프트 직접입력 (레포 기본 지시문 4종을 대체)",
                key="copy_instr_custom",
                height=100,
                placeholder="예: Render the supplied ad copy as poster typography. ...",
            )

    st.subheader("④ 유저 프롬프트")

    def _fill_user_prompt_test() -> None:
        if st.session_state.get("user_prompt_test_chk"):
            st.session_state["user_prompt"] = "test"

    st.checkbox(
        "체크하면 입력창에 'test' 문구가 들어갑니다",
        key="user_prompt_test_chk",
        on_change=_fill_user_prompt_test,
    )
    user_prompt = st.text_area(
        "유저 프롬프트 입력 (서비스의 사용자 요청란과 동일하게 프롬프트에 반영됨)",
        key="user_prompt",
        height=80,
        placeholder="예: 더 따뜻하고 아늑한 카페 분위기로",
    )

    st.subheader("⑤ 실행")
    col_a, col_b = st.columns(2)
    with col_a:
        count = st.number_input("제작(테스트) 갯수", min_value=1, max_value=10, key="count")
    with col_b:
        quality = st.selectbox("품질", ["low", "medium", "high"], key="quality")

    settings_preview = load_settings()
    cost = int(count) * calculate_image_cost(None, quality=quality)
    st.caption(
        f"모델 {settings_preview.openai_image_model} · {int(count)}장 · "
        f"예상 비용 ≈ ${cost:.3f} ({quality} 품질 단가 기준, 실제는 토큰 기반으로 계산됨)"
    )

    def collect_cfg() -> dict | None:
        if not image_file:
            st.error("메뉴 사진을 넣어주세요.")
            return None
        if channel_label == DIRECT and not channel_custom.strip():
            st.error("채널 프롬프트를 입력해주세요.")
            return None
        if detail_label == DIRECT and not detail_custom.strip():
            st.error("유형 프롬프트를 입력해주세요.")
            return None
        # 문구 빈칸은 막지 않는다 — 서비스와 동일하게 generate_ad_copy가
        # 채널/유형/유저 프롬프트 맥락으로 문구를 자동 생성한다.
        return {
            "name": (name or "test").strip().replace(" ", "-")[:40],
            "count": int(count),
            "quality": quality,
            "image_name": image_file.name,
            "image_bytes": image_file.getvalue(),
            "image_data_url": _to_data_url(image_file),
            "channel_id": preset.id if preset else "custom",
            "channel_label": channel_label,
            "channel_hint": preset.prompt_hint if preset else channel_custom.strip(),
            "channel_prompt": preset.channel_prompt if preset else "",
            "detail_id": detail.id if detail else "custom",
            "detail_label": detail.label if detail else DIRECT,
            "detail_hint": detail.prompt_hint if detail else detail_custom.strip(),
            "api_size": api_size,
            "target_w": target_w,
            "target_h": target_h,
            "user_prompt": user_prompt.strip(),
            "copy_on": copy_on,
            "copy_text": copy_text.strip(),
            "copy_mode": copy_mode,
            "copy_mode_custom": copy_mode_custom.strip(),
            "copy_instr_custom": copy_instr_custom.strip(),
        }

    col_run, col_preview = st.columns(2)
    with col_preview:
        if st.button("프롬프트 미리보기", use_container_width=True):
            cfg = collect_cfg()
            if cfg:
                st.session_state["preview_prompt"] = assemble_full_prompt(
                    cfg, preview_ad_copy(cfg)
                )
    with col_run:
        if st.button("생성하기", type="primary", use_container_width=True):
            cfg = collect_cfg()
            if cfg and not load_settings().openai_api_key:
                st.error("OPENAI_API_KEY가 없습니다 (.env 확인).")
            elif cfg:
                run_id = start_run(cfg)
                st.session_state.pop("preview_prompt", None)
                st.session_state["_reset_test_name"] = True
                st.session_state["_flash"] = (
                    f"생성 시작: {cfg['name']} — 완료되면 '결과 · 평가' 탭에 나타납니다. "
                    "기다리지 않고 바로 다음 테스트를 설정할 수 있습니다."
                )
                st.rerun()

    if st.session_state.get("preview_prompt"):
        with st.expander("조립된 프롬프트 전문", expanded=True):
            if copy_on and copy_mode in {"polish", "rewrite"}:
                st.caption("다듬기/바꾸기 모드는 실행 시 AI가 변환한 문구로 대체됩니다.")
            st.code(st.session_state["preview_prompt"], language=None)

    # 최근 완료 + 실행 현황
    st.divider()
    progress_entries = []
    for path in RUNS_DIR.glob("*/progress.json"):
        try:
            progress_entries.append((path, json.loads(path.read_text(encoding="utf-8"))))
        except (ValueError, OSError):
            continue
    done_entries = [(p, g) for p, g in progress_entries if g.get("status") == "done"]
    if done_entries:
        latest_path, latest = max(done_entries, key=lambda pg: pg[1].get("ended", ""))
        st.info(
            f"최근 완료된 테스트: **{latest.get('name', latest_path.parent.name)}** "
            f"({latest.get('ended', '')} · 성공 {latest.get('ok', 0)} / "
            f"실패 {latest.get('error', 0)}) "
            "→ '결과 · 평가' 탭에서 확인"
        )

    st.subheader("실행 현황")
    col_r1, col_r2 = st.columns([1, 3])
    with col_r1:
        if st.button("새로고침"):
            st.rerun()
    with col_r2:
        auto = st.checkbox("자동 새로고침 (3초)", key="auto_refresh")

    progress_entries.sort(key=lambda pg: pg[0].stat().st_mtime, reverse=True)
    any_running = False
    for path, prog in progress_entries[:5]:
        total = max(int(prog.get("total", 1)), 1)
        done = int(prog.get("done", 0))
        status = prog.get("status", "?")
        any_running = any_running or status == "running"
        icon = {"running": "▶", "done": "✓", "failed": "✕"}.get(status, "·")
        st.progress(
            min(done / total, 1.0),
            text=(
                f"{icon} {prog.get('name', path.parent.name)} — {done}/{total} "
                f"(성공 {prog.get('ok', 0)} / 실패 {prog.get('error', 0)})"
                + (f" — {prog.get('message', '')}" if status == "failed" else "")
                + (f" · 실패 사유: {prog.get('last_error', '')}" if prog.get("last_error") else "")
            ),
        )
    if not progress_entries:
        st.caption("아직 실행한 테스트가 없습니다.")
    if auto and any_running:
        time.sleep(3)
        st.rerun()
