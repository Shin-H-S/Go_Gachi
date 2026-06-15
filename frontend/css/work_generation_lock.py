WORK_GENERATION_LOCK_CSS = """
div[role="radiogroup"] label:not(:has(input:checked)) {
    opacity: 0.34;
    pointer-events: none;
}

div[role="radiogroup"] label:has(input:checked) {
    opacity: 1;
}

.channel-tab:not(.is-active),
div[data-testid="stSegmentedControl"]
    button:not([aria-pressed="true"]):not([data-selected="true"]) {
    opacity: 0.34;
    pointer-events: none;
}

div[data-testid="stElementContainer"]:has(.channel-button-marker)
    + div[data-testid="stHorizontalBlock"]
    button[data-testid="stBaseButton-secondary"] {
    opacity: 0.34;
    pointer-events: none;
}

.channel-tab.is-active,
div[data-testid="stSegmentedControl"] button[aria-pressed="true"],
div[data-testid="stSegmentedControl"] button[data-selected="true"] {
    opacity: 1;
}

div[data-testid="stElementContainer"]:has(.channel-button-marker)
    + div[data-testid="stHorizontalBlock"]
    button[data-testid="stBaseButton-primary"] {
    opacity: 1;
}

div[data-testid="stButton"] button[kind="primary"],
div[data-testid="stButton"] button[data-testid="stBaseButton-primary"] {
    background: #aab7b3 !important;
    color: #eef3f1 !important;
    -webkit-text-fill-color: #eef3f1 !important;
    box-shadow: none !important;
    cursor: not-allowed !important;
    pointer-events: none;
}

div[data-testid="stButton"] button[kind="primary"] *,
div[data-testid="stButton"] button[data-testid="stBaseButton-primary"] * {
    color: #eef3f1 !important;
    -webkit-text-fill-color: #eef3f1 !important;
}
"""
