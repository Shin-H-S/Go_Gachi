from html import escape

import streamlit as st

COPY_MODE_LABELS = {
    "preserve": "그대로 사용",
    "polish": "자연스럽게 다듬기",
    "rewrite": "홍보 문구로 바꾸기",
}


def _line(label: str, value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return (
        '<div class="result-copy-line">'
        f"<span>{escape(label)}</span>"
        f"<strong>{escape(text)}</strong>"
        "</div>"
    )


def render_result_copy(copy: dict[str, object] | None) -> None:
    if not copy:
        return

    mode = str(copy.get("copyMode") or "")
    mode_label = COPY_MODE_LABELS.get(mode, mode or "문구")
    lines = [
        _line("헤드라인", copy.get("headline")),
        _line("서브카피", copy.get("subcopy")),
        _line("CTA", copy.get("cta")),
    ]
    body = "".join(line for line in lines if line)
    if not body:
        return

    st.markdown(
        (
            '<div class="result-copy-panel">'
            f'<div class="result-copy-mode">{escape(mode_label)}</div>'
            f"{body}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
