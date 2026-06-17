from html import escape
from pathlib import Path

import streamlit as st

from frontend.core.router import navigate_to
from frontend.media.image_data import bytes_to_data_url


MAIN_SLIDE_ASSET_DIR = (
    Path(__file__).resolve().parents[1] / "assets" / "main" / "optimized"
)
MAIN_HERO_SLIDES = (
    {
        "filename": "main-slide-01.webp",
        "eyebrow": "당근마켓",
        "title": "메뉴 이미지",
        "alt": "당근마켓 메뉴 이미지 미리보기",
        "class_name": "blue-panel-one",
    },
    {
        "filename": "main-slide-02.webp",
        "eyebrow": "인스타그램",
        "title": "정사각형 피드",
        "alt": "인스타그램 정사각형 피드 이미지 미리보기",
        "class_name": "blue-panel-two",
    },
    {
        "filename": "main-slide-03.webp",
        "eyebrow": "당근마켓",
        "title": "메뉴 이미지",
        "alt": "당근마켓 메뉴 이미지 미리보기",
        "class_name": "blue-panel-three",
    },
    {
        "filename": "main-slide-04.webp",
        "eyebrow": "배달의 민족",
        "title": "단색 배경 이미지",
        "alt": "배달의 민족 단색 배경 이미지 미리보기",
        "class_name": "blue-panel-four",
    },
    {
        "filename": "main-slide-05.webp",
        "eyebrow": "인스타그램",
        "title": "정사각형 피드",
        "alt": "인스타그램 정사각형 피드 이미지 미리보기",
        "class_name": "blue-panel-five",
    },
)


def _main_slide_image_src(filename: str) -> str:
    return bytes_to_data_url((MAIN_SLIDE_ASSET_DIR / filename).read_bytes(), "image/webp")


def _build_hero_visual_html() -> str:
    panels = []
    loop_slides = (*MAIN_HERO_SLIDES, MAIN_HERO_SLIDES[0])

    for index, slide in enumerate(loop_slides):
        filename = str(slide["filename"])
        class_name = escape(str(slide["class_name"]))
        eyebrow = escape(str(slide["eyebrow"]))
        title = escape(str(slide["title"]))
        alt = escape(str(slide["alt"]))
        loading = "eager" if index == 0 else "lazy"
        image_src = _main_slide_image_src(filename)

        panels.append(
            "\n".join(
                (
                    f'<article class="blue-panel {class_name}">',
                    '<div class="blue-panel-image-stage">',
                    (
                        f'<img class="blue-panel-image" src="{image_src}" '
                        f'alt="{alt}" loading="{loading}" />'
                    ),
                    "</div>",
                    '<div class="blue-panel-caption">',
                    f"<span>{eyebrow}</span>",
                    f"<strong>{title}</strong>",
                    "</div>",
                    "</article>",
                )
            )
        )

    slides_html = "\n".join(panels)
    return "\n".join(
        (
            '<section class="hero-visual" aria-label="Go Gachi AI ad preview carousel">',
            '<div class="blue-slide-window">',
            '<div class="blue-slide-track">',
            slides_html,
            "</div>",
            "</div>",
            "</section>",
        )
    )


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
        st.markdown(
            """
            <nav class="landing-nav" aria-label="Go Gachi navigation">
                <div class="landing-brand">Go Gachi<span>*</span></div>
                <div class="landing-auth">
                    <a class="landing-login" href="?page=login" target="_self">로그인</a>
                    <a class="landing-signup" href="?page=signup" target="_self">회원가입</a>
                </div>
            </nav>
            """,
            unsafe_allow_html=True,
        )

        hero_left, hero_right = st.columns([0.55, 0.45], gap="large")

        with hero_left:
            st.markdown(
                """
                <section
                    class="main-landing"
                    aria-label="사장님의 메뉴 사진을 광고 이미지로 바꾸는 가장 빠른 방법"
                >
                    <p class="hero-kicker">AI CAFE AD MAKER</p>
                    <h1 class="hero-title">
                        사장님의 메뉴 사진을<br />
                        광고 이미지로 바꾸는<br />
                        가장 빠른 방법
                    </h1>
                    <p class="hero-copy">
                        메뉴 사진을 올리고 채널을 고르면, 인스타그램과 배달앱에 바로 쓸 수
                        있는 광고 이미지를 빠르게 만들어드립니다.
                    </p>
                </section>
                """,
                unsafe_allow_html=True,
            )

            st.markdown('<div class="main-start-button-marker"></div>', unsafe_allow_html=True)
            if st.button("무료로 시작하기", key="main-start-button"):
                _handle_start_click()

        with hero_right:
            st.markdown(_build_hero_visual_html(), unsafe_allow_html=True)
