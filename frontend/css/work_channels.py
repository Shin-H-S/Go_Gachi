WORK_CHANNELS_CSS = """
.channel-tabs {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
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
"""
