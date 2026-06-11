from html import escape

import streamlit as st

from frontend.work.copy import copy_mode_label


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

    mode_label = copy_mode_label(copy.get("copyMode"))
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
