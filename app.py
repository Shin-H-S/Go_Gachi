import requests
import streamlit as st


st.set_page_config(
    page_title="Go Gachi - 광고 이미지 생성기",
    page_icon="🍽️",
    layout="wide",
)

API_URL = "http://127.0.0.1:8000/api/v1/generate"

INDUSTRY_MAP = {
    "음식점": "restaurant",
}

MOOD_MAP = {
    "깔끔": "clean",
    "따뜻": "warm",
    "귀여움": "cute",
    "감성": "aesthetic",
}

MOOD_DESCRIPTIONS = {
    "깔끔": "선명한 메뉴 사진과 정돈된 문구",
    "따뜻": "동네 가게 같은 포근한 분위기",
    "귀여움": "밝고 친근한 홍보 이미지",
    "감성": "SNS에 올리기 좋은 세련된 톤",
}


st.markdown(
    """
    <style>
        :root {
            --ink: #17201f;
            --muted: #66706d;
            --line: #dce6e2;
            --paper: #fbfcf8;
            --mint: #0f8f7f;
            --mint-dark: #07675b;
            --coral: #f26a4f;
            --sun: #f3bb45;
            --panel: rgba(255, 255, 255, 0.88);
        }

        .stApp {
            background:
                radial-gradient(circle at 12% 12%, rgba(15, 143, 127, 0.18), transparent 30%),
                radial-gradient(circle at 88% 5%, rgba(242, 106, 79, 0.14), transparent 28%),
                linear-gradient(135deg, #f7fbf8 0%, #fff8ef 48%, #f4faf9 100%);
            color: var(--ink);
        }

        .block-container {
            max-width: 1120px;
            padding-top: 2.2rem;
            padding-bottom: 4rem;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        .hero {
            border: 1px solid rgba(23, 32, 31, 0.09);
            border-radius: 8px;
            padding: 34px 34px 28px;
            background:
                linear-gradient(120deg, rgba(255,255,255,0.94), rgba(255,255,255,0.76)),
                linear-gradient(135deg, rgba(15,143,127,0.12), rgba(242,106,79,0.10));
            box-shadow: 0 18px 55px rgba(28, 54, 49, 0.12);
            position: relative;
            overflow: hidden;
            margin-bottom: 22px;
        }

        .hero:after {
            content: "";
            position: absolute;
            right: -58px;
            bottom: -72px;
            width: 260px;
            height: 260px;
            border: 38px solid rgba(15, 143, 127, 0.10);
            border-radius: 50%;
        }

        .brand-row {
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--mint-dark);
            font-size: 0.88rem;
            font-weight: 800;
            letter-spacing: 0;
            margin-bottom: 16px;
        }

        .brand-mark {
            display: inline-flex;
            width: 34px;
            height: 34px;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            background: var(--mint);
            color: white;
            box-shadow: 0 10px 20px rgba(15, 143, 127, 0.24);
        }

        .hero h1 {
            max-width: 680px;
            margin: 0;
            color: var(--ink);
            font-size: clamp(2.1rem, 4.6vw, 4.7rem);
            line-height: 1.03;
            letter-spacing: 0;
            font-weight: 900;
        }

        .hero p {
            max-width: 620px;
            margin: 18px 0 0;
            color: #46524f;
            font-size: 1.08rem;
            line-height: 1.7;
        }

        .step-strip {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 10px;
            margin-top: 24px;
            max-width: 760px;
        }

        .step-chip {
            border: 1px solid rgba(15, 143, 127, 0.18);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.72);
            padding: 12px 14px;
            color: #31403d;
            font-size: 0.9rem;
            font-weight: 700;
        }

        .panel {
            border: 1px solid rgba(23, 32, 31, 0.10);
            border-radius: 8px;
            background: var(--panel);
            box-shadow: 0 14px 36px rgba(35, 54, 49, 0.10);
            padding: 24px;
            min-height: 100%;
        }

        .panel-title {
            margin: 0 0 4px;
            color: var(--ink);
            font-size: 1.16rem;
            font-weight: 850;
        }

        .panel-note {
            margin: 0 0 18px;
            color: var(--muted);
            font-size: 0.92rem;
            line-height: 1.55;
        }

        .preview-empty {
            display: flex;
            min-height: 270px;
            align-items: center;
            justify-content: center;
            border: 1px dashed rgba(15, 143, 127, 0.42);
            border-radius: 8px;
            background:
                linear-gradient(135deg, rgba(15, 143, 127, 0.08), rgba(242, 106, 79, 0.07)),
                rgba(255, 255, 255, 0.48);
            color: #65736f;
            text-align: center;
            padding: 28px;
            line-height: 1.7;
            font-weight: 650;
        }

        .mood-help {
            margin-top: -6px;
            margin-bottom: 16px;
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.55;
        }

        .status-card {
            border-left: 4px solid var(--mint);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.74);
            padding: 14px 16px;
            color: #3d4946;
            font-size: 0.92rem;
            line-height: 1.55;
            margin: 18px 0;
        }

        .result-wrap {
            margin-top: 22px;
            border: 1px solid rgba(23, 32, 31, 0.10);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.90);
            padding: 24px;
            box-shadow: 0 16px 40px rgba(35, 54, 49, 0.11);
        }

        div[data-testid="stFileUploader"] section {
            border-color: rgba(15, 143, 127, 0.30);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.65);
        }

        div[role="radiogroup"] {
            gap: 10px;
        }

        div[role="radiogroup"] label {
            border: 1px solid rgba(23, 32, 31, 0.12);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.70);
            padding: 10px 13px;
            min-height: 42px;
        }

        .stButton > button,
        .stDownloadButton > button {
            min-height: 50px;
            border-radius: 8px;
            border: 0;
            background: linear-gradient(135deg, var(--mint), var(--mint-dark));
            color: white;
            font-weight: 850;
            box-shadow: 0 14px 24px rgba(15, 143, 127, 0.23);
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            border: 0;
            background: linear-gradient(135deg, #12a28f, #075f54);
            color: white;
            transform: translateY(-1px);
        }

        [data-testid="stImage"] img {
            border-radius: 8px;
            border: 1px solid rgba(23, 32, 31, 0.10);
        }

        @media (max-width: 720px) {
            .block-container {
                padding-top: 1rem;
            }

            .hero {
                padding: 26px 20px;
            }

            .step-strip {
                grid-template-columns: 1fr;
            }

            .panel {
                padding: 20px;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <section class="hero">
        <div class="brand-row">
            <span class="brand-mark">G</span>
            <span>GO GACHI AD STUDIO</span>
        </div>
        <h1>메뉴 사진 한 장으로 광고 이미지를 완성하세요</h1>
        <p>
            소상공인을 위한 간단한 광고 이미지 생성 도구입니다.
            메뉴 사진을 올리고 원하는 분위기를 고르면 홍보용 이미지를 만들어드립니다.
        </p>
        <div class="step-strip">
            <div class="step-chip">1. 메뉴 사진 업로드</div>
            <div class="step-chip">2. 분위기 선택</div>
            <div class="step-chip">3. 광고 이미지 생성</div>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

upload_col, option_col = st.columns([1.08, 0.92], gap="large")

with upload_col:
    st.markdown(
        """
        <div class="panel">
            <h2 class="panel-title">메뉴 사진</h2>
            <p class="panel-note">밝고 선명한 사진일수록 결과물이 더 자연스럽게 만들어집니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "음식점 메뉴 사진 1장",
        type=["jpg", "jpeg", "png", "webp"],
        help="JPG, PNG, WEBP 파일을 업로드할 수 있습니다.",
        label_visibility="collapsed",
    )

    if uploaded_file:
        st.image(uploaded_file, caption="업로드된 메뉴 사진", use_container_width=True)
    else:
        st.markdown(
            """
            <div class="preview-empty">
                메뉴 사진을 업로드하면 이곳에서 바로 미리볼 수 있습니다.<br>
                음식이 잘 보이는 정면 사진을 추천합니다.
            </div>
            """,
            unsafe_allow_html=True,
        )

with option_col:
    st.markdown(
        """
        <div class="panel">
            <h2 class="panel-title">광고 설정</h2>
            <p class="panel-note">가게의 분위기에 맞는 톤을 선택해 주세요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    industry_label = st.radio(
        "업종",
        options=list(INDUSTRY_MAP.keys()),
        horizontal=True,
    )
    industry_value = INDUSTRY_MAP[industry_label]

    mood_label = st.radio(
        "분위기",
        options=list(MOOD_MAP.keys()),
        horizontal=True,
    )
    mood_value = MOOD_MAP[mood_label]

    st.markdown(
        f"""
        <div class="mood-help">
            선택한 분위기: <strong>{mood_label}</strong><br>
            {MOOD_DESCRIPTIONS[mood_label]}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="status-card">
            생성 버튼을 누르면 백엔드 API로 사진과 설정이 전달됩니다.
            결과가 나오기까지 최대 60초 정도 걸릴 수 있습니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    generate = st.button("광고 이미지 생성", type="primary", use_container_width=True)


if generate:
    if not uploaded_file:
        st.warning("사진을 먼저 업로드해주세요.")
    else:
        with st.spinner("광고 이미지를 생성 중입니다... 최대 60초 정도 걸릴 수 있어요."):
            try:
                resp = requests.post(
                    API_URL,
                    files={
                        "image": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type,
                        )
                    },
                    data={
                        "industry": industry_value,
                        "mood": mood_value,
                    },
                    timeout=60,
                )

                if resp.status_code == 200:
                    image_url = resp.json().get("image_url")
                    if image_url:
                        st.markdown('<div class="result-wrap">', unsafe_allow_html=True)
                        st.success("이미지 생성 완료!")
                        st.subheader("생성된 광고 이미지")
                        st.image(image_url, use_container_width=True)

                        img_data = requests.get(image_url, timeout=30)
                        if img_data.status_code == 200:
                            st.download_button(
                                label="이미지 다운로드",
                                data=img_data.content,
                                file_name="gachi_ad.png",
                                mime="image/png",
                                use_container_width=True,
                            )
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.error("서버 응답에 image_url이 없습니다.")

                else:
                    detail = resp.json().get("detail", "알 수 없는 오류")
                    st.error(f"오류 {resp.status_code}: {detail}")

            except requests.exceptions.ConnectionError:
                st.error(
                    "백엔드 서버에 연결할 수 없습니다.\n\n"
                    "`uvicorn main:app --reload` 로 서버를 먼저 실행해주세요."
                )
            except requests.exceptions.Timeout:
                st.error("요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.")
            except Exception as e:
                st.error(f"예상치 못한 오류: {e}")
