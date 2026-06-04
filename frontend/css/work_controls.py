WORK_CONTROLS_CSS = """
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
"""
