WORK_SELECTION_CSS = """
div[data-testid="stSegmentedControl"] {
    width: 100% !important;
    max-width: none !important;
}

div[data-testid="stSegmentedControl"] > div,
div[data-testid="stSegmentedControl"] [data-baseweb="button-group"],
div[data-testid="stSegmentedControl"] [role="group"],
div[data-testid="stSegmentedControl"] div:has(> button) {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)) !important;
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

.st-key-text_overlay_enabled label,
.st-key-text_overlay_enabled label *,
.st-key-text_overlay_enabled p {
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
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

.st-key-copy_mode_label div[data-testid="stRadio"] > label:not([data-baseweb="radio"]) {
    border: 0 !important;
    border-radius: 0 !important;
    background: #ffffff !important;
    padding: 0 !important;
    min-height: 0 !important;
    color: var(--ink) !important;
    font-size: 15px !important;
    font-weight: 800 !important;
}

.st-key-copy_mode_label div[data-testid="stRadio"] > label:not([data-baseweb="radio"]) * {
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
    font-size: 15px !important;
    font-weight: 800 !important;
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
"""
