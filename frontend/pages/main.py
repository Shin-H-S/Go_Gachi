import streamlit as st

from frontend.core.router import navigate_to
from frontend.main.hero_visual import build_hero_visual_html
from frontend.main.navigation import render_main_navigation

HERO_ARIA_LABEL = (
    "\uc0ac\uc7a5\ub2d8\uc758 \uba54\ub274 \uc0ac\uc9c4\uc744 "
    "\uad11\uace0 \uc774\ubbf8\uc9c0\ub85c \ubc14\uafb8\ub294 "
    "\uac00\uc7a5 \ube60\ub978 \ubc29\ubc95"
)
HERO_TITLE_LINES = (
    "\uc0ac\uc7a5\ub2d8\uc758 \uba54\ub274 \uc0ac\uc9c4\uc744",
    "\uad11\uace0 \uc774\ubbf8\uc9c0\ub85c \ubc14\uafb8\ub294",
    "\uac00\uc7a5 \ube60\ub978 \ubc29\ubc95",
)
HERO_COPY = (
    "\uba54\ub274 \uc0ac\uc9c4\uc744 \uc62c\ub9ac\uace0 "
    "\ucc44\ub110\uc744 \uace0\ub974\uba74 "
    "\uc778\uc2a4\ud0c0\uadf8\ub7a8\uacfc \ubc30\ub2ec\uc571\uc5d0 "
    "\ubc14\ub85c \uc4f8 \uc218 \uc788\ub294 \uad11\uace0 "
    "\uc774\ubbf8\uc9c0\ub97c \ube60\ub974\uac8c "
    "\ub9cc\ub4e4\uc5b4\ub4dc\ub9bd\ub2c8\ub2e4."
)
START_BUTTON_LABEL = "\ubb34\ub8cc\ub85c \uc2dc\uc791\ud558\uae30"


def _handle_start_click() -> None:
    st.session_state["auth_redirect_page"] = ""
    navigate_to("work")
    st.rerun()


def render_main_page() -> None:
    st.markdown(
        """
        <style>
            .main .block-container,
            [data-testid="stMainBlockContainer"] {
                max-width: none !important;
                padding: 0 !important;
            }

            [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {
                gap: 0 !important;
                width: 100% !important;
            }

            [data-testid="stHeader"],
            [data-testid="stToolbar"],
            [data-testid="stDecoration"],
            #MainMenu,
            footer {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="main-landing"):
        render_main_navigation()

        hero_left, hero_right = st.columns([0.55, 0.45], gap="large")

        with hero_left:
            st.markdown(
                f"""
                <section
                    class="main-landing"
                    aria-label="{HERO_ARIA_LABEL}"
                >
                    <p class="hero-kicker">AI CAFE AD MAKER</p>
                    <h1 class="hero-title">
                        {HERO_TITLE_LINES[0]}<br />
                        {HERO_TITLE_LINES[1]}<br />
                        {HERO_TITLE_LINES[2]}
                    </h1>
                    <p class="hero-copy">
                        {HERO_COPY}
                    </p>
                </section>
                """,
                unsafe_allow_html=True,
            )

            st.markdown('<div class="main-start-button-marker"></div>', unsafe_allow_html=True)
            if st.button(START_BUTTON_LABEL, key="main-start-button"):
                _handle_start_click()

        with hero_right:
            st.markdown(build_hero_visual_html(), unsafe_allow_html=True)
