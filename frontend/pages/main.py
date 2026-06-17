import streamlit as st

from frontend.core.router import navigate_to
from frontend.main.hero_visual import build_hero_visual_html
from frontend.main.navigation import render_main_navigation


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
                """
                <section
                    class="main-landing"
                    aria-label="?ъ옣?섏쓽 硫붾돱 ?ъ쭊??愿묎퀬 ?대?吏濡?諛붽씀??媛??鍮좊Ⅸ 諛⑸쾿"
                >
                    <p class="hero-kicker">AI CAFE AD MAKER</p>
                    <h1 class="hero-title">
                        ?ъ옣?섏쓽 硫붾돱 ?ъ쭊??br />
                        愿묎퀬 ?대?吏濡?諛붽씀??br />
                        媛??鍮좊Ⅸ 諛⑸쾿
                    </h1>
                    <p class="hero-copy">
                        硫붾돱 ?ъ쭊???щ━怨?梨꾨꼸??怨좊Ⅴ硫? ?몄뒪?洹몃옩怨?諛곕떖?깆뿉 諛붾줈 ????
                        ?덈뒗 愿묎퀬 ?대?吏瑜?鍮좊Ⅴ寃?留뚮뱾?대뱶由쎈땲??
                    </p>
                </section>
                """,
                unsafe_allow_html=True,
            )

            st.markdown('<div class="main-start-button-marker"></div>', unsafe_allow_html=True)
            if st.button("臾대즺濡??쒖옉?섍린", key="main-start-button"):
                _handle_start_click()

        with hero_right:
            st.markdown(build_hero_visual_html(), unsafe_allow_html=True)
