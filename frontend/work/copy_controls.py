import httpx
import streamlit as st

from frontend.services.api_client import BACKEND_URL, request_auto_copy
from frontend.work.copy import COPY_MODE_OPTIONS


def _copy_to_text(copy: dict[str, object]) -> str:
    lines = []
    for label, key in (
        ("헤드라인", "headline"),
        ("서브카피", "subcopy"),
        ("CTA", "cta"),
    ):
        value = str(copy.get(key) or "").strip()
        if value:
            lines.append(f"{label}: {value}")
    return "\n".join(lines)


def _fill_auto_copy(format_label: str, detail_label: str, image_prompt: str) -> None:
    try:
        copy = request_auto_copy(
            image_prompt,
            format_label,
            detail_label,
            access_token=st.session_state.get("auth_access_token", ""),
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 501:
            message = "백엔드 자동 광고 문구 생성 기능이 아직 준비되지 않았습니다."
        else:
            message = (
                f"백엔드 자동 광고 문구 요청 실패 "
                f"[HTTP {exc.response.status_code}]: {exc.response.text}"
            )
        st.session_state["auto_copy_status"] = message
        return
    except httpx.HTTPError as exc:
        st.session_state["auto_copy_status"] = (
            f"백엔드 연결 실패 [NETWORK_ERROR] {BACKEND_URL}: {type(exc).__name__}: {exc}"
        )
        return
    except Exception as exc:
        st.session_state["auto_copy_status"] = f"자동 광고 문구 생성 중 오류가 발생했습니다: {exc}"
        return

    generated_copy = _copy_to_text(copy)
    if not generated_copy:
        st.session_state["auto_copy_status"] = "백엔드 응답에 표시할 광고 문구가 없습니다."
        return

    st.session_state["ad_copy_prompt"] = generated_copy
    st.session_state.pop("auto_copy_status", None)


def render_copy_controls(
    format_label: str,
    detail_label: str,
    image_prompt: str = "",
) -> tuple[str, bool, str]:
    text_overlay_enabled = st.checkbox(
        "광고 문구 포함",
        value=True,
        key="text_overlay_enabled",
    )
    raw_prompt = st.text_area(
        "광고 문구",
        placeholder=(
            "직접 넣고 싶은 광고 문구를 입력하세요.\n"
            "비워두면 자동 문구 생성을 요청합니다."
        ),
        height=150,
        disabled=not text_overlay_enabled,
        key="ad_copy_prompt",
        help="비워두면 이미지 생성 시 자동 문구 생성을 요청합니다.",
        label_visibility="collapsed",
    )
    if text_overlay_enabled:
        st.button(
            "광고 문구 자동 생성",
            key="auto_copy_generate",
            on_click=_fill_auto_copy,
            args=(format_label, detail_label, image_prompt),
            use_container_width=True,
        )
        auto_copy_status = st.session_state.pop("auto_copy_status", None)
        if auto_copy_status:
            st.info(auto_copy_status)

    prompt = raw_prompt if text_overlay_enabled else ""
    copy_mode_labels = [label for label, _mode in COPY_MODE_OPTIONS]
    copy_mode_by_label = dict(COPY_MODE_OPTIONS)
    copy_mode_label = st.radio(
        "문구 처리 방식",
        options=copy_mode_labels,
        index=0,
        horizontal=False,
        key="copy_mode_label",
        disabled=not text_overlay_enabled,
    )
    copy_mode = copy_mode_by_label.get(copy_mode_label, "preserve")
    if not text_overlay_enabled:
        copy_mode = "preserve"
    return prompt, text_overlay_enabled, copy_mode

