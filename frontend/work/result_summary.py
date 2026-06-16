from html import escape

import streamlit as st


def _status_chip(label: str, *, included: bool) -> str:
    state_class = "is-included" if included else "is-excluded"
    return f'<span class="result-summary-chip {state_class}">' f"{escape(label)}" "</span>"


def result_summary_html(result_context: dict[str, object] | None) -> str:
    if not result_context:
        return ""

    has_ad_copy = bool(result_context.get("adCopyEnabled"))
    ad_copy_label = "광고 문구 포함" if has_ad_copy else "광고 문구 미포함"
    chips = [_status_chip(ad_copy_label, included=has_ad_copy)]

    return '<div class="result-summary-panel">' f"{''.join(chips)}" "</div>"


def render_result_summary(result_context: dict[str, object] | None) -> None:
    html = result_summary_html(result_context)
    if not html:
        return

    st.markdown(html, unsafe_allow_html=True)
