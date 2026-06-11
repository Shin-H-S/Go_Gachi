from html import escape

import streamlit as st


def _status_chip(label: str, *, included: bool) -> str:
    state_class = "is-included" if included else "is-excluded"
    return (
        f'<span class="result-summary-chip {state_class}">'
        f"{escape(label)}"
        "</span>"
    )


def render_result_summary(result_context: dict[str, object] | None) -> None:
    if not result_context:
        return

    has_ad_copy = bool(result_context.get("adCopyEnabled"))
    has_logo = bool(result_context.get("logoUploadHash"))
    ad_copy_label = "광고 문구 포함" if has_ad_copy else "광고 문구 미포함"
    logo_label = "로고 포함" if has_logo else "로고 미포함"

    st.markdown(
        (
            '<div class="result-summary-panel">'
            f"{_status_chip(ad_copy_label, included=has_ad_copy)}"
            f"{_status_chip(logo_label, included=has_logo)}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
