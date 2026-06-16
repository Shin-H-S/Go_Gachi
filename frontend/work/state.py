import hashlib

import streamlit as st

from frontend.core.config import FORMAT_OPTIONS, get_detail_id, get_detail_size


def _state(session_state=None):
    return st.session_state if session_state is None else session_state


def clear_result_state(session_state=None) -> None:
    """현재 표시 중인 생성 결과(미러)를 세션에서 제거한다."""
    state = _state(session_state)
    state.pop("result_bytes", None)
    state.pop("result_image_url", None)
    state.pop("result_copy", None)
    state.pop("result_context", None)


def get_result_history(session_state=None) -> list:
    history = _state(session_state).get("result_history")
    return history if isinstance(history, list) else []


def get_result_cursor(session_state=None) -> int:
    """0 = 원본(업로드 이미지), 1..N = N번째 생성 결과."""
    state = _state(session_state)
    total = len(get_result_history(state))
    cursor = state.get("result_cursor", total)
    try:
        cursor = int(cursor)
    except (TypeError, ValueError):
        cursor = total
    return max(0, min(cursor, total))


def reset_result_history(session_state=None) -> None:
    state = _state(session_state)
    state["result_history"] = []
    state["result_cursor"] = 0
    clear_result_state(state)


def apply_cursor_to_result_state(session_state=None) -> None:
    """현재 커서가 가리키는 결과를 result_* 미러(다운로드/헤더용)에 반영한다."""
    state = _state(session_state)
    history = get_result_history(state)
    cursor = get_result_cursor(state)
    if cursor >= 1 and history:
        entry = history[cursor - 1]
        image_bytes = entry.get("bytes")
        if isinstance(image_bytes, bytes):
            state["result_bytes"] = image_bytes
        else:
            state.pop("result_bytes", None)
        image_url = entry.get("url")
        if image_url:
            state["result_image_url"] = image_url
        else:
            state.pop("result_image_url", None)
        state["result_copy"] = entry.get("copy")
        state["result_context"] = entry.get("context")
    else:
        clear_result_state(state)


def append_result_to_history(entry: dict, session_state=None) -> None:
    state = _state(session_state)
    history = list(get_result_history(state))
    history.append(entry)
    state["result_history"] = history
    state["result_cursor"] = len(history)
    apply_cursor_to_result_state(state)


def move_result_cursor(delta: int, session_state=None) -> None:
    state = _state(session_state)
    total = len(get_result_history(state))
    cursor = get_result_cursor(state)
    state["result_cursor"] = max(0, min(total, cursor + delta))
    apply_cursor_to_result_state(state)


def build_result_context(
    uploaded_file,
    prompt: str,
    format_label: str,
    detail_label: str,
    *,
    ad_copy_prompt: str = "",
    copy_mode: str = "preserve",
    ad_copy_enabled: bool = True,
):
    """생성 결과가 어떤 입력 조건에서 만들어졌는지 비교할 키를 만든다."""
    if not uploaded_file:
        return None

    target_size = get_detail_size(format_label, detail_label)
    upload_hash = hashlib.sha256(uploaded_file.getvalue()).hexdigest()
    return {
        "presetId": FORMAT_OPTIONS[format_label]["value"],
        "detailType": get_detail_id(format_label, detail_label),
        "targetWidth": target_size[0],
        "targetHeight": target_size[1],
        "prompt": prompt.strip(),
        "adCopyPrompt": ad_copy_prompt.strip(),
        "copyMode": copy_mode,
        "adCopyEnabled": ad_copy_enabled,
        "uploadHash": upload_hash,
    }


def sync_result_state(current_context, session_state=None) -> None:
    """업로드된 원본이 바뀐 경우에만 생성 이력을 초기화한다.

    같은 원본에서 프롬프트/설정만 바꿔 여러 번 생성한 결과는 화살표로
    계속 탐색할 수 있어야 하므로, 업로드(uploadHash)가 바뀔 때만 리셋한다.
    """
    state = _state(session_state)
    current_hash = current_context.get("uploadHash") if current_context else None
    has_result = any(
        key in state
        for key in (
            "result_bytes",
            "result_image_url",
            "result_copy",
            "result_context",
            "result_history",
        )
    )
    if current_hash is not None:
        should_reset = state.get("result_history_upload") != current_hash
    elif current_context is None:
        should_reset = has_result or state.get("result_history_upload") is not None
    else:
        should_reset = state.get("result_history_upload") is not None or (
            has_result and state.get("result_context") != current_context
        )

    if should_reset:
        state["result_history_upload"] = current_hash
        reset_result_history(state)


def get_selected_channel() -> str:
    default_label = next(iter(FORMAT_OPTIONS))
    selected_label = st.session_state.get("selected_channel", default_label)
    if selected_label not in FORMAT_OPTIONS:
        selected_label = default_label
        st.session_state["selected_channel"] = selected_label

    return selected_label
