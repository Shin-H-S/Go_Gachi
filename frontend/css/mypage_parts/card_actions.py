MYPAGE_CARD_ACTIONS_CSS = """
.st-key-mypage-shell [class*="st-key-mypage-action-original-"] a,
.st-key-mypage-shell [class*="st-key-mypage-action-original-"] button,
.st-key-mypage-shell [class*="st-key-mypage-action-original-"] div[data-testid="stLinkButton"] a,
.st-key-mypage-shell [class*="st-key-mypage-action-original-"] div[data-testid="stButton"] button,
.st-key-mypage-shell [class*="st-key-mypage-action-download-"] button,
.st-key-mypage-shell [class*="st-key-mypage-action-download-"]
    div[data-testid="stDownloadButton"] button,
.st-key-mypage-shell [class*="st-key-mypage-action-folder-"] button,
.st-key-mypage-shell [class*="st-key-mypage-action-folder-"] div[data-testid="stButton"] button {
    height: 42px !important;
    min-height: 42px !important;
    padding: 0 14px !important;
    box-sizing: border-box !important;
    display: flex !important;
    align-items: center;
    justify-content: center;
    border: 1px solid #ddd9cf !important;
    border-radius: 8px !important;
    background: #fbfaf6 !important;
    box-shadow: 0 1px 3px rgba(28, 33, 31, 0.08) !important;
    color: #394b4a !important;
    -webkit-text-fill-color: #394b4a !important;
    font-size: 13px !important;
    font-weight: 900 !important;
    line-height: 1 !important;
}

.st-key-mypage-shell [class*="st-key-mypage-action-download-"] button,
.st-key-mypage-shell [class*="st-key-mypage-action-download-"]
    div[data-testid="stDownloadButton"] button {
    background: #fbfaf6 !important;
    border-color: #ddd9cf !important;
    color: #394b4a !important;
    -webkit-text-fill-color: #394b4a !important;
}

.st-key-mypage-shell [class*="st-key-mypage-action-download-"] button:disabled,
.st-key-mypage-shell [class*="st-key-mypage-action-original-"] button:disabled,
.st-key-mypage-shell [class*="st-key-mypage-action-folder-"] button:disabled {
    background: #f4f1ea !important;
    border-color: #e1ded5 !important;
    color: #a6aba8 !important;
    -webkit-text-fill-color: #a6aba8 !important;
    opacity: 1;
}

.st-key-mypage-shell [class*="st-key-mypage-action-folder-select"] div[data-baseweb="select"] {
    min-height: 42px !important;
}

.st-key-mypage-shell [class*="st-key-mypage-action-folder-select"]
    div[data-baseweb="select"] > div {
    min-height: 42px !important;
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

.st-key-mypage-shell [class*="st-key-mypage-action-original-"] a p,
.st-key-mypage-shell [class*="st-key-mypage-action-original-"] button p,
.st-key-mypage-shell [class*="st-key-mypage-action-download-"] button p,
.st-key-mypage-shell [class*="st-key-mypage-action-folder-"] button p {
    margin: 0;
    line-height: 1 !important;
}
"""
