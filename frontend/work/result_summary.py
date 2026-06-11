from html import escape

import streamlit as st

from frontend.work.logo_positions import LOGO_POSITION_LABELS


def _status_chip(label: str, *, included: bool) -> str:
    state_class = "is-included" if included else "is-excluded"
    return f'<span class="result-summary-chip {state_class}">' f"{escape(label)}" "</span>"


def _logo_summary(result_context: dict[str, object]) -> tuple[bool, str | None, bool]:
    logo = result_context.get("logo")
    if isinstance(logo, dict) and "used" in logo:
        position = logo.get("position")
        return (
            bool(logo.get("used")),
            str(position) if position else None,
            True,
        )

    has_logo = bool(result_context.get("logoUploadHash"))
    position = result_context.get("logoPosition") if has_logo else None
    return has_logo, str(position) if position else None, False


def _logo_position_label(position: str) -> str:
    korean_label = LOGO_POSITION_LABELS.get(position)
    if korean_label:
        return f"logo.position: {position} ({korean_label})"
    return f"logo.position: {position}"


def render_result_summary(result_context: dict[str, object] | None) -> None:
    if not result_context:
        return

    has_ad_copy = bool(result_context.get("adCopyEnabled"))
    has_logo, logo_position, has_backend_logo = _logo_summary(result_context)
    ad_copy_label = "광고 문구 포함" if has_ad_copy else "광고 문구 미포함"
    logo_label = (
        ("로고 적용됨" if has_logo else "로고 미적용")
        if has_backend_logo
        else ("로고 포함" if has_logo else "로고 미포함")
    )

    chips = [
        _status_chip(ad_copy_label, included=has_ad_copy),
        _status_chip(logo_label, included=has_logo),
    ]
    if has_backend_logo:
        chips.append(_status_chip(f"logo.used: {str(has_logo).lower()}", included=has_logo))
    if logo_position:
        chips.append(_status_chip(_logo_position_label(logo_position), included=has_logo))

    st.markdown(
        ('<div class="result-summary-panel">' f"{''.join(chips)}" "</div>"),
        unsafe_allow_html=True,
    )
