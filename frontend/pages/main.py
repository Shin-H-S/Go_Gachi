import streamlit as st


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
                <div class="landing-menu">
                    <span>서비스</span>
                    <span>템플릿</span>
                    <span>활용법</span>
                    <span>요금</span>
                </div>
                <div class="landing-auth">
                    <span class="landing-login">로그인</span>
                    <span class="landing-signup">회원가입</span>
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

            cta_input_col, cta_button_col = st.columns([0.48, 0.52], gap="small")
            with cta_input_col:
                st.markdown(
                    '<div class="landing-url-chip">go-gachi.ai/우리카페</div>',
                    unsafe_allow_html=True,
                )
            with cta_button_col:
                st.markdown(
                    (
                        '<a class="landing-start-link" href="?page=work" '
                        'target="_self">무료로 시작하기</a>'
                    ),
                    unsafe_allow_html=True,
                )

        with hero_right:
            st.markdown(
                """
                <section class="hero-visual" aria-label="moving blue preview placeholder">
                    <div class="blue-slide-window">
                        <div class="blue-slide-track">
                            <div class="blue-panel">
                                <span>오늘의 메뉴</span>
                                <strong>신메뉴 광고</strong>
                            </div>
                            <div class="blue-panel blue-panel-two">
                                <span>카페 채널</span>
                                <strong>SNS 배너</strong>
                            </div>
                            <div class="blue-panel blue-panel-three">
                                <span>배달앱</span>
                                <strong>할인 프로모션</strong>
                            </div>
                            <div class="blue-panel">
                                <span>오늘의 메뉴</span>
                                <strong>신메뉴 광고</strong>
                            </div>
                        </div>
                    </div>
                </section>
                """,
                unsafe_allow_html=True,
            )

