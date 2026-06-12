import hashlib

import streamlit as st

from frontend.core.config import FORMAT_OPTIONS, get_detail_id, get_detail_size


def clear_result_state() -> None:
    """현재 입력과 맞지 않는 생성 결과를 세션에서 제거한다."""
    st.session_state.pop("result_bytes", None)
    st.session_state.pop("result_copy", None)
    st.session_state.pop("result_context", None)


def build_result_context(
    uploaded_file,
    prompt: str,
    format_label: str,
    detail_label: str,
    *,
    ad_copy_prompt: str = "",
    copy_mode: str = "preserve",
    ad_copy_enabled: bool = True,
    logo_file=None,
    logo_position: str = "bottom_right",
):
    """생성 결과가 어떤 입력 조건에서 만들어졌는지 비교할 키를 만든다."""
    if not uploaded_file:
        return None

    target_size = get_detail_size(format_label, detail_label)
    upload_hash = hashlib.sha256(uploaded_file.getvalue()).hexdigest()
    logo_upload_hash = (
        hashlib.sha256(logo_file.getvalue()).hexdigest() if logo_file is not None else None
    )
    return {
        "presetId": FORMAT_OPTIONS[format_label]["value"],
        "detailType": get_detail_id(format_label, detail_label),
        "targetWidth": target_size[0],
        "targetHeight": target_size[1],
        "prompt": prompt.strip(),
        "adCopyPrompt": ad_copy_prompt.strip(),
        "copyMode": copy_mode,
        "adCopyEnabled": ad_copy_enabled,
        "logoUploadHash": logo_upload_hash,
        "logoPosition": logo_position,
        "uploadHash": upload_hash,
    }


def sync_result_state(current_context) -> None:
    """입력 조건이 바뀐 경우 이전 생성 결과를 숨긴다."""
    if "result_bytes" not in st.session_state:
        st.session_state.pop("result_context", None)
        return

    if st.session_state.get("result_context") != current_context:
        clear_result_state()


def get_selected_channel() -> str:
    default_label = next(iter(FORMAT_OPTIONS))
    selected_label = st.session_state.get("selected_channel", default_label)
    if selected_label not in FORMAT_OPTIONS:
        selected_label = default_label
        st.session_state["selected_channel"] = selected_label

    return selected_label
