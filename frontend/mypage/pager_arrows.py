from functools import cache
from pathlib import Path

import streamlit as st

from frontend.media.image_data import bytes_to_data_url

_ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"


@cache
def _arrow_data_url(filename: str) -> str:
    return bytes_to_data_url((_ASSET_DIR / filename).read_bytes())


def render_pagination_arrow_css(key: str) -> None:
    """Inject CSS that turns the prev/next pagination buttons into arrow icons.

    The arrows are drawn as a button ``::after`` overlay (so they never fight the
    button ``background`` shorthand), and the selectors carry
    ``button[data-testid^="stBaseButton"]`` specificity (0,2,1) so the styling
    wins in the base state, not just on hover.
    """
    prev_src = _arrow_data_url("pointer_left.png")
    next_src = _arrow_data_url("pointer_right.png")
    st.markdown(
        f"""
        <style>
        .st-key-{key}-prev button[data-testid^="stBaseButton"],
        .st-key-{key}-next button[data-testid^="stBaseButton"] {{
            position: relative !important;
            font-size: 0 !important;
            border: 2px solid rgba(32, 39, 37, 0.12) !important;
            border-radius: 6px !important;
            background: linear-gradient(180deg, #ffffff 0%, #f4f4f4 100%) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.75),
                0 8px 18px rgba(44, 47, 42, 0.08) !important;
        }}
        .st-key-{key}-prev button[data-testid^="stBaseButton"]:hover,
        .st-key-{key}-next button[data-testid^="stBaseButton"]:hover {{
            border: 2px solid rgba(15, 143, 127, 0.28) !important;
            background: linear-gradient(180deg, #ffffff 0%, #ededed 100%) !important;
        }}
        .st-key-{key}-prev button[data-testid^="stBaseButton"]::after,
        .st-key-{key}-next button[data-testid^="stBaseButton"]::after {{
            content: "";
            position: absolute;
            inset: 0;
            background-repeat: no-repeat;
            background-position: center;
            background-size: auto 50%;
            pointer-events: none;
        }}
        .st-key-{key}-prev button[data-testid^="stBaseButton"]::after {{
            background-image: url("{prev_src}");
        }}
        .st-key-{key}-next button[data-testid^="stBaseButton"]::after {{
            background-image: url("{next_src}");
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
