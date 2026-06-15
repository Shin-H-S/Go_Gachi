MYPAGE_CARD_ACTIONS_CSS = """
.st-key-mypage-shell [class*="st-key-mypage-action-work-from-image"] {
    --mypage-toolbar-action-bg: #5a463c;
    --mypage-toolbar-action-hover: #4c3a31;
}

.st-key-mypage-shell [class*="st-key-mypage-action-original"] {
    --mypage-toolbar-action-bg: #34383d;
    --mypage-toolbar-action-hover: #2c3034;
}

.st-key-mypage-shell [class*="st-key-mypage-action-download"] {
    --mypage-toolbar-action-bg: #53613b;
    --mypage-toolbar-action-hover: #465233;
}

.st-key-mypage-shell [class*="st-key-mypage-action-folder"] {
    --mypage-toolbar-action-bg: #39467a;
    --mypage-toolbar-action-hover: #313c69;
}

.st-key-mypage-shell [class*="st-key-mypage-action-original"] a,
.st-key-mypage-shell [class*="st-key-mypage-action-original"] button,
.st-key-mypage-shell [class*="st-key-mypage-action-original"] div[data-testid="stLinkButton"] a,
.st-key-mypage-shell [class*="st-key-mypage-action-original"] div[data-testid="stButton"] button,
.st-key-mypage-shell [class*="st-key-mypage-action-work-from-image"] button,
.st-key-mypage-shell [class*="st-key-mypage-action-work-from-image"]
    div[data-testid="stButton"] button,
.st-key-mypage-shell [class*="st-key-mypage-action-download"] a,
.st-key-mypage-shell [class*="st-key-mypage-action-download"] button,
.st-key-mypage-shell [class*="st-key-mypage-action-download"] div[data-testid="stLinkButton"] a,
.st-key-mypage-shell [class*="st-key-mypage-action-download"]
    div[data-testid="stDownloadButton"] button,
.st-key-mypage-shell [class*="st-key-mypage-action-folder"] button,
.st-key-mypage-shell [class*="st-key-mypage-action-folder"] div[data-testid="stButton"] button {
    height: 53px !important;
    min-height: 53px !important;
    width: 100% !important;
    min-width: 0 !important;
    padding: 0 18px !important;
    box-sizing: border-box !important;
    display: flex !important;
    align-items: center;
    justify-content: center;
    border: 0 !important;
    border-radius: 8px !important;
    background: var(--mypage-toolbar-action-bg) !important;
    box-shadow: 0 2px 5px rgba(24, 28, 31, 0.16) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 16.25px !important;
    font-weight: 900 !important;
    line-height: 1 !important;
    text-decoration: none !important;
    white-space: nowrap !important;
    word-break: keep-all !important;
}

.st-key-mypage-shell [class*="st-key-mypage-action-original"] a:hover,
.st-key-mypage-shell [class*="st-key-mypage-action-original"] button:hover:not(:disabled),
.st-key-mypage-shell [class*="st-key-mypage-action-work-from-image"] button:hover:not(:disabled),
.st-key-mypage-shell [class*="st-key-mypage-action-download"] a:hover,
.st-key-mypage-shell [class*="st-key-mypage-action-download"] button:hover:not(:disabled),
.st-key-mypage-shell [class*="st-key-mypage-action-folder"] button:hover:not(:disabled) {
    border: 0 !important;
    background: var(--mypage-toolbar-action-hover) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

.st-key-mypage-shell [class*="st-key-mypage-action-work-from-image"],
.st-key-mypage-shell [class*="st-key-mypage-action-original"],
.st-key-mypage-shell [class*="st-key-mypage-action-download"],
.st-key-mypage-shell [class*="st-key-mypage-action-folder"] {
    width: 100%;
    min-width: 0;
}

.st-key-mypage-shell [class*="st-key-mypage-action-download"] button:disabled,
.st-key-mypage-shell [class*="st-key-mypage-action-original"] button:disabled,
.st-key-mypage-shell [class*="st-key-mypage-action-work-from-image"] button:disabled,
.st-key-mypage-shell [class*="st-key-mypage-action-folder"] button:disabled {
    border: 0 !important;
    background: var(--mypage-toolbar-action-bg) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 0.58;
}

.st-key-mypage-shell [class*="st-key-mypage-action-select-all"] {
    width: min(100%, calc(267px * 0.6));
}

.st-key-mypage-shell [class*="st-key-mypage-action-select-all"] button,
.st-key-mypage-shell [class*="st-key-mypage-action-select-all"]
    div[data-testid="stButton"] button {
    height: 53px !important;
    min-height: 53px !important;
    padding: 0 18px !important;
    box-sizing: border-box !important;
    display: flex !important;
    align-items: center;
    justify-content: center;
    border: 1px solid #ddd9cf !important;
    border-radius: 8px !important;
    background: #fbfaf6 !important;
    box-shadow: 0 1px 3px rgba(28, 33, 31, 0.08) !important;
    color: #00a6a6 !important;
    -webkit-text-fill-color: #00a6a6 !important;
    font-size: 16.25px !important;
    font-weight: 900 !important;
    line-height: 1 !important;
    white-space: nowrap !important;
    word-break: keep-all !important;
}

.st-key-mypage-shell [class*="st-key-mypage-action-select-all"] button:disabled {
    background: #f4f1ea !important;
    border-color: #e1ded5 !important;
    opacity: 1;
}

.st-key-mypage-shell [class*="st-key-mypage-action-select-all-active"] button,
.st-key-mypage-shell [class*="st-key-mypage-action-select-all-active"]
    div[data-testid="stButton"] button {
    border-width: 3px !important;
    border-color: #00a6a6 !important;
    box-shadow: 0 0 0 1px rgba(0, 166, 166, 0.16) !important;
}

.st-key-mypage-shell [class*="st-key-mypage-action-folder-select"] div[data-baseweb="select"] {
    min-height: 53px !important;
}

.st-key-mypage-shell [class*="st-key-mypage-action-folder-select"]
    div[data-baseweb="select"] > div {
    min-height: 53px !important;
    border: 1px solid #e4e0d8 !important;
    border-radius: 8px !important;
    background: #f2f5f3 !important;
    box-shadow: none !important;
}

.st-key-mypage-shell [class*="st-key-mypage-action-folder-select"] div[data-baseweb="select"] span,
.st-key-mypage-shell [class*="st-key-mypage-action-folder-select"] div[data-baseweb="select"] svg {
    color: #9aa4a0 !important;
    -webkit-text-fill-color: #9aa4a0 !important;
}

.st-key-mypage-shell [class*="st-key-mypage-action-original"] a p,
.st-key-mypage-shell [class*="st-key-mypage-action-original"] button p,
.st-key-mypage-shell [class*="st-key-mypage-action-select-all"] button p,
.st-key-mypage-shell [class*="st-key-mypage-action-work-from-image"] button p,
.st-key-mypage-shell [class*="st-key-mypage-action-download"] a p,
.st-key-mypage-shell [class*="st-key-mypage-action-download"] button p,
.st-key-mypage-shell [class*="st-key-mypage-action-folder"] button p {
    margin: 0;
    line-height: 1 !important;
    white-space: nowrap !important;
}

.st-key-mypage-shell [class*="st-key-mypage-action-original"] a p,
.st-key-mypage-shell [class*="st-key-mypage-action-original"] button p,
.st-key-mypage-shell [class*="st-key-mypage-action-work-from-image"] button p,
.st-key-mypage-shell [class*="st-key-mypage-action-download"] a p,
.st-key-mypage-shell [class*="st-key-mypage-action-download"] button p,
.st-key-mypage-shell [class*="st-key-mypage-action-folder"] button p {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
"""
