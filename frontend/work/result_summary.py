from html import escape

import streamlit as st


def _status_chip(label: str, *, included: bool) -> str:
    state_class = "is-included" if included else "is-excluded"
    return f'<span class="result-summary-chip {state_class}">' f"{escape(label)}" "</span>"


def render_result_summary(result_context: dict[str, object] | None) -> None:
    if not result_context:
        return

    has_ad_copy = bool(result_context.get("adCopyEnabled"))
    ad_copy_label = "광고 문구 포함" if has_ad_copy else "광고 문구 미포함"

    chips = [_status_chip(ad_copy_label, included=has_ad_copy)]

    st.markdown(
        ('<div class="result-summary-panel">' f"{''.join(chips)}" "</div>"),
        unsafe_allow_html=True,
    )
