import streamlit as st


def add_css() -> None:
    st.markdown(
        """
        <style>
            :root {
                --paper: #f8f7f2;
                --panel: #fffdf8;
                --ink: #202725;
                --muted: #66716d;
                --line: #dfded6;
                --teal: #0f8f7f;
                --teal-dark: #087163;
            }

            html,
            body,
            .stApp,
            [data-testid="stAppViewContainer"] {
                color-scheme: light;
            }

            .stApp {
                background: linear-gradient(180deg, #f4f1e9 0%, #fbfaf4 48%, #f1f7f5 100%);
                color: var(--ink);
            }

            .main .block-container {
                max-width: 1360px;
                padding: 24px 28px 40px;
            }

            [data-testid="stHeader"] {
                background: transparent;
            }

            h1, h2, h3, p {
                letter-spacing: 0;
            }

            .topbar {
                padding-bottom: 18px;
                border-bottom: 1px solid rgba(32, 39, 37, 0.12);
                margin-bottom: 20px;
            }

            .brand-kicker {
                color: var(--teal-dark);
                font-size: 13px;
                font-weight: 900;
                margin: 0 0 8px;
            }

            .title {
                color: var(--ink);
                font-size: clamp(36px, 5vw, 62px);
                line-height: 1.02;
                font-weight: 950;
                margin: 0;
            }

            .section-label,
            p.section-label {
                color: #3a4240;
                font-size: 20px !important;
                font-weight: 900;
                margin: 0 0 8px;
            }

            .small-note {
                color: var(--muted);
                font-size: 13px;
                line-height: 1.55;
                margin: 0 0 12px;
            }

            .format-readout {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                border: 1px solid rgba(32, 39, 37, 0.12);
                border-radius: 8px;
                background: #f5f4ee;
                padding: 12px 14px;
                margin: 6px 0 14px;
                color: #29312f;
                font-size: 13px;
                font-weight: 800;
            }

            .format-readout .channel-name {
                color: var(--ink);
                font-size: 17px;
                font-weight: 950;
                line-height: 1.2;
            }

            .format-readout .format-size {
                color: var(--ink);
                font-size: 18px;
                font-weight: 950;
                line-height: 1;
                white-space: nowrap;
            }

            .format-readout strong,
            .format-readout small {
                display: block;
            }

            .format-readout small {
                color: var(--muted);
                font-size: 12px;
                font-weight: 700;
                margin-top: 4px;
            }

            .detail-choice-label,
            p.detail-choice-label {
                color: #3a4240;
                font-size: 20px !important;
                font-weight: 900;
                margin: 0 0 8px;
            }

            .st-key-left-upload-section,
            .st-key-left-channel-section,
            .st-key-left-type-section,
            .st-key-left-prompt-section {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1px solid rgba(32, 39, 37, 0.14) !important;
                border-radius: 8px !important;
                box-shadow: 0 10px 22px rgba(44, 47, 42, 0.055);
            }

            .st-key-left-upload-section > div,
            .st-key-left-channel-section > div,
            .st-key-left-type-section > div,
            .st-key-left-prompt-section > div,
            .st-key-left-upload-section [data-testid="stVerticalBlockBorderWrapper"],
            .st-key-left-channel-section [data-testid="stVerticalBlockBorderWrapper"],
            .st-key-left-type-section [data-testid="stVerticalBlockBorderWrapper"],
            .st-key-left-prompt-section [data-testid="stVerticalBlockBorderWrapper"],
            .st-key-left-upload-section [data-testid="stVerticalBlock"],
            .st-key-left-channel-section [data-testid="stVerticalBlock"],
            .st-key-left-type-section [data-testid="stVerticalBlock"],
            .st-key-left-prompt-section [data-testid="stVerticalBlock"] {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 0 !important;
                box-shadow: none !important;
            }

            .preview-shell {
                height: 620px;
                border: 1px solid rgba(32, 39, 37, 0.13);
                border-radius: 8px;
                background:
                    linear-gradient(45deg, rgba(32,39,37,0.035) 25%, transparent 25%),
                    linear-gradient(-45deg, rgba(32,39,37,0.035) 25%, transparent 25%),
                    linear-gradient(45deg, transparent 75%, rgba(32,39,37,0.035) 75%),
                    linear-gradient(-45deg, transparent 75%, rgba(32,39,37,0.035) 75%),
                    #fbfaf4;
                background-size: 28px 28px;
                background-position: 0 0, 0 14px, 14px -14px, -14px 0;
                padding: 18px;
                box-sizing: border-box;
                overflow: hidden;
            }

            .result-caption {
                display: flex;
                justify-content: space-between;
                gap: 12px;
                color: #5d6764;
                font-size: 13px;
                font-weight: 800;
                margin: 0 0 10px;
            }

            .empty-guide {
                display: flex;
                height: calc(100% - 28px);
                align-items: center;
                justify-content: center;
                text-align: center;
                color: #5d6764;
                font-size: 18px;
                font-weight: 900;
                line-height: 1.65;
            }

            .loading-state {
                display: flex;
                height: calc(100% - 28px);
                align-items: flex-start;
                justify-content: center;
                padding-top: 150px;
                box-sizing: border-box;
                text-align: center;
            }

            .loading-panel {
                display: inline-flex;
                flex-direction: column;
                align-items: center;
                gap: 16px;
                color: #4d5960;
                font-size: 18px;
                font-weight: 900;
                line-height: 1.55;
            }

            .loading-spinner {
                width: 54px;
                height: 54px;
                border-radius: 999px;
                border: 6px solid rgba(108, 94, 214, 0.14);
                border-top-color: #5145c6;
                border-right-color: #a790ff;
                animation: spin 0.85s linear infinite;
            }

            .preview-image-frame {
                height: calc(100% - 28px);
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: hidden;
            }

            .preview-image-frame img {
                display: block;
                max-width: 100%;
                max-height: 100%;
                width: auto;
                height: auto;
                object-fit: contain;
                border-radius: 8px;
                border: 1px solid rgba(32, 39, 37, 0.12);
                box-sizing: border-box;
            }

            @keyframes spin {
                from {
                    transform: rotate(0deg);
                }
                to {
                    transform: rotate(360deg);
                }
            }

            .stTextArea textarea,
            div[data-testid="stTextArea"] textarea,
            textarea {
                border-radius: 8px;
                background: #f5f4ee !important;
                color: var(--ink) !important;
                -webkit-text-fill-color: var(--ink) !important;
                caret-color: var(--teal);
            }

            .stTextArea textarea::placeholder,
            div[data-testid="stTextArea"] textarea::placeholder,
            textarea::placeholder {
                color: #7a8793 !important;
                -webkit-text-fill-color: #7a8793 !important;
                opacity: 1 !important;
            }

            div[data-testid="stButton"] button,
            div[data-testid="stDownloadButton"] button,
            button[data-testid^="stBaseButton"] {
                min-height: 48px;
                border-radius: 8px;
                border: 1px solid rgba(32, 39, 37, 0.14) !important;
                background: linear-gradient(180deg, #f5f4ee 0%, #e8e6de 100%) !important;
                color: #29312f !important;
                -webkit-text-fill-color: #29312f !important;
                font-weight: 900;
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.75), 0 8px 18px rgba(44, 47, 42, 0.08);
            }

            div[data-testid="stButton"] button *,
            div[data-testid="stDownloadButton"] button *,
            button[data-testid^="stBaseButton"] * {
                color: inherit !important;
                -webkit-text-fill-color: inherit !important;
            }

            div[data-testid="stButton"] button[kind="primary"],
            div[data-testid="stButton"] button[data-testid="stBaseButton-primary"] {
                min-height: 48px;
                border-radius: 8px;
                border: 1px solid var(--teal-dark) !important;
                background: var(--teal) !important;
                color: white !important;
                -webkit-text-fill-color: white !important;
                font-weight: 900;
                box-shadow: 0 12px 24px rgba(15, 143, 127, 0.22);
            }

            div[data-testid="stButton"] button[kind="primary"] *,
            div[data-testid="stButton"] button[data-testid="stBaseButton-primary"] * {
                color: white !important;
                -webkit-text-fill-color: white !important;
            }

            div[data-testid="stButton"] button[kind="primary"]:hover,
            div[data-testid="stButton"] button[data-testid="stBaseButton-primary"]:hover {
                border: 1px solid var(--teal-dark) !important;
                background: var(--teal-dark) !important;
                color: white !important;
                -webkit-text-fill-color: white !important;
            }

            div[data-testid="stElementContainer"]:has(.generate-button-marker)
                + div[data-testid="stElementContainer"] button,
            div[data-testid="stElementContainer"]:has(.generate-button-marker)
                + div[data-testid="stButton"] button {
                min-height: 58px !important;
                border-radius: 999px !important;
                border: 1px solid #0f4cbd !important;
                background:
                    linear-gradient(90deg, #062d70 0%, #0c4db8 58%, #76b8ff 100%)
                    !important;
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
                font-size: 18px !important;
                font-weight: 950 !important;
                box-shadow: 0 12px 24px rgba(20, 79, 189, 0.24);
            }

            div[data-testid="stElementContainer"]:has(.generate-button-marker)
                + div[data-testid="stElementContainer"] button *,
            div[data-testid="stElementContainer"]:has(.generate-button-marker)
                + div[data-testid="stButton"] button * {
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
                font-size: 18px !important;
                font-weight: 950 !important;
            }

            div[data-testid="stElementContainer"]:has(.generate-button-marker)
                + div[data-testid="stElementContainer"] button:hover,
            div[data-testid="stElementContainer"]:has(.generate-button-marker)
                + div[data-testid="stButton"] button:hover {
                border: 1px solid #0b3e9e !important;
                background:
                    linear-gradient(90deg, #05275f 0%, #0a45a5 58%, #65aaf4 100%)
                    !important;
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
            }

            .tool-row {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 8px;
                margin-top: 10px;
            }

            .tool-row .stButton > button,
            .tool-row .stDownloadButton > button {
                min-height: 58px;
                border: 1px solid rgba(32, 39, 37, 0.12);
                border-radius: 4px;
                background: linear-gradient(180deg, #f5f4ee 0%, #e8e6de 100%) !important;
                color: #29312f !important;
                -webkit-text-fill-color: #29312f !important;
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.75), 0 8px 18px rgba(44, 47, 42, 0.08);
                font-size: 28px;
                font-weight: 900;
            }

            .tool-row .stButton > button:hover,
            .tool-row .stDownloadButton > button:hover {
                border: 1px solid rgba(15, 143, 127, 0.28);
                background: linear-gradient(180deg, #ffffff 0%, #d7e5e1 100%) !important;
                color: #0b6f63 !important;
                -webkit-text-fill-color: #0b6f63 !important;
            }

            div[data-testid="stFileUploader"] section {
                border: 1px dashed rgba(15, 143, 127, 0.42);
                border-radius: 8px;
                background: #f5f4ee !important;
                color: var(--ink) !important;
            }

            div[data-testid="stFileUploaderFile"],
            div[data-testid="stFileUploaderFile"] > div,
            div[data-testid="stFileUploaderDropzone"] {
                background: #f5f4ee !important;
                color: var(--ink) !important;
            }

            div[data-testid="stFileUploader"] section *,
            div[data-testid="stFileUploaderFile"] *,
            div[data-testid="stFileUploaderDropzone"] * {
                color: var(--ink) !important;
                -webkit-text-fill-color: var(--ink) !important;
            }

            div[data-testid="stFileUploader"] button {
                background: #ffffff !important;
                color: var(--ink) !important;
                -webkit-text-fill-color: var(--ink) !important;
                border: 1px solid rgba(32, 39, 37, 0.14) !important;
            }

            div[role="radiogroup"] {
                gap: 6px;
            }

            .channel-tabs {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 8px;
                width: 100%;
                margin: 0 0 14px;
            }

            .channel-tab {
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 84px;
                border: 1px solid rgba(32, 39, 37, 0.14);
                border-radius: 8px;
                background: #f5f4ee;
                color: var(--ink) !important;
                -webkit-text-fill-color: var(--ink) !important;
                font-size: 18px;
                font-weight: 900;
                line-height: 1.2;
                text-align: center;
                text-decoration: none !important;
                box-sizing: border-box;
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.75), 0 8px 18px rgba(44, 47, 42, 0.08);
            }

            .channel-tab:hover {
                border-color: rgba(15, 143, 127, 0.45);
                background: #eef8f5;
                color: var(--ink) !important;
                -webkit-text-fill-color: var(--ink) !important;
                text-decoration: none !important;
            }

            .channel-tab.is-active {
                border-color: var(--teal-dark);
                background: var(--teal);
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
            }

            div[data-testid="stElementContainer"]:has(.channel-button-marker)
                + div[data-testid="stHorizontalBlock"] {
                width: 100% !important;
            }

            div[data-testid="stElementContainer"]:has(.channel-button-marker)
                + div[data-testid="stHorizontalBlock"] div[data-testid="column"] {
                min-width: 0 !important;
            }

            .channel-card-media {
                display: flex;
                align-items: center;
                justify-content: center;
                height: 128px;
                padding: 18px 20px;
                border: 1px solid rgba(32, 39, 37, 0.14);
                border-bottom: 0;
                border-radius: 8px 8px 0 0;
                background: #ffffff;
                box-sizing: border-box;
                overflow: hidden;
                box-shadow:
                    inset 0 1px 0 rgba(255,255,255,0.75),
                    0 8px 18px rgba(44, 47, 42, 0.055);
            }

            .channel-card-media.is-active {
                border-color: var(--teal-dark);
                background: #eef8f5;
            }

            .channel-card-media img {
                display: block;
                width: 100%;
                height: 100%;
                object-fit: contain;
            }

            .channel-card-placeholder {
                color: var(--ink);
                font-size: 16px;
                font-weight: 900;
                text-align: center;
                line-height: 1.35;
            }

            div[data-testid="stElementContainer"]:has(.channel-card-media) {
                margin-bottom: 0 !important;
            }

            div[data-testid="stElementContainer"]:has(.channel-button-marker)
                + div[data-testid="stHorizontalBlock"] button {
                min-height: 58px !important;
                width: 100% !important;
                border-radius: 0 0 8px 8px !important;
                border-top: 0 !important;
                font-size: 15px !important;
                font-weight: 900 !important;
                line-height: 1.2 !important;
                word-break: keep-all !important;
            }

            div[data-testid="stElementContainer"]:has(.channel-button-marker)
                + div[data-testid="stHorizontalBlock"] button * {
                font-size: 15px !important;
                font-weight: 900 !important;
                line-height: 1.2 !important;
                word-break: keep-all !important;
            }

            div[data-testid="stSegmentedControl"] {
                width: 100% !important;
                max-width: none !important;
            }

            div[data-testid="stSegmentedControl"] > div,
            div[data-testid="stSegmentedControl"] [data-baseweb="button-group"],
            div[data-testid="stSegmentedControl"] [role="group"],
            div[data-testid="stSegmentedControl"] div:has(> button) {
                display: grid !important;
                grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
                width: 100% !important;
                max-width: none !important;
                gap: 8px !important;
            }

            div[data-testid="stSegmentedControl"] button {
                width: 100% !important;
                min-width: 0 !important;
                max-width: none !important;
                flex: 1 1 0 !important;
                min-height: 84px;
                border-radius: 8px !important;
                border: 1px solid rgba(32, 39, 37, 0.14) !important;
                background: #f5f4ee !important;
                color: var(--ink) !important;
                -webkit-text-fill-color: var(--ink) !important;
                font-size: 18px !important;
                font-weight: 900 !important;
                line-height: 1.2 !important;
            }

            div[data-testid="stSegmentedControl"] button[aria-pressed="true"],
            div[data-testid="stSegmentedControl"] button[data-selected="true"] {
                border-color: rgba(15, 143, 127, 0.45) !important;
                background: #eef8f5 !important;
                color: var(--ink) !important;
                -webkit-text-fill-color: var(--ink) !important;
            }

            div[data-testid="stSegmentedControl"] button * {
                color: var(--ink) !important;
                -webkit-text-fill-color: var(--ink) !important;
                font-size: 18px !important;
                font-weight: 900 !important;
                line-height: 1.2 !important;
            }

            div[data-testid="stRadio"] label,
            div[role="radiogroup"] label {
                border: 1px solid rgba(32, 39, 37, 0.12);
                border-radius: 8px;
                background: #f5f4ee !important;
                color: var(--ink) !important;
                padding: 8px 10px;
                min-height: 40px;
            }

            div[data-testid="stRadio"] label[data-baseweb="radio"] input[type="radio"] {
                accent-color: #ff5a5f !important;
            }

            div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input[type="radio"])
                > div:first-child {
                background-color: #ffffff !important;
                border: 1px solid rgba(32, 39, 37, 0.22) !important;
                box-shadow: inset 0 0 0 2px #ffffff !important;
            }

            div[data-testid="stRadio"] label[data-baseweb="radio"]:has(
                input[type="radio"]:not(:checked)
            ) > div:first-child > div {
                background-color: #ffffff !important;
            }

            div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input[type="radio"]:checked)
                > div:first-child {
                background-color: #ff5a5f !important;
                border-color: #ff5a5f !important;
            }

            div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input[type="radio"]:checked)
                > div:first-child > div {
                background-color: #ffffff !important;
            }

            div[data-testid="stRadio"] label *,
            div[role="radiogroup"] label *,
            div[role="radiogroup"] label p {
                color: var(--ink) !important;
                -webkit-text-fill-color: var(--ink) !important;
            }

            [data-testid="stImage"] img {
                border-radius: 8px;
                border: 1px solid rgba(32, 39, 37, 0.12);
            }

            @media (max-width: 900px) {
                .main .block-container {
                    padding: 18px 14px 32px;
                }

                .preview-shell {
                    height: 360px;
                }

            }
        </style>
        """,
        unsafe_allow_html=True,
    )
