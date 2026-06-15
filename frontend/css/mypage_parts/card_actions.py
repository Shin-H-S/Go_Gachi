MYPAGE_CARD_ACTIONS_CSS = """
.st-key-mypage-shell [class*="st-key-mypage-original-"] a,
.st-key-mypage-shell [class*="st-key-mypage-original-"] button,
.st-key-mypage-shell [class*="st-key-mypage-original-"] div[data-testid="stLinkButton"] a,
.st-key-mypage-shell [class*="st-key-mypage-original-"] div[data-testid="stButton"] button,
.st-key-mypage-shell [class*="st-key-mypage-download-"] a,
.st-key-mypage-shell [class*="st-key-mypage-download-"] div[data-testid="stLinkButton"] a,
.st-key-mypage-shell [class*="st-key-mypage-download-"] button,
.st-key-mypage-shell [class*="st-key-mypage-download-"] div[data-testid="stDownloadButton"] button {
    height: 34px !important;
    min-height: 34px !important;
    padding: 0 10px !important;
    box-sizing: border-box !important;
    display: flex !important;
    align-items: center;
    justify-content: center;
    border-width: 1px !important;
    border-style: solid !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    font-size: 13px !important;
    font-weight: 900 !important;
    line-height: 1 !important;
}

.st-key-mypage-shell [class*="st-key-mypage-original-"] a,
.st-key-mypage-shell [class*="st-key-mypage-original-"] button {
    background: #f5f4ee !important;
    border-color: #d7d2c7 !important;
    color: #46524f !important;
    -webkit-text-fill-color: #46524f !important;
}

.st-key-mypage-shell [class*="st-key-mypage-download-"] button,
.st-key-mypage-shell [class*="st-key-mypage-download-"] a,
.st-key-mypage-shell [class*="st-key-mypage-download-"] div[data-testid="stLinkButton"] a,
.st-key-mypage-shell [class*="st-key-mypage-download-"] div[data-testid="stDownloadButton"] button {
    background: #eaf4ff !important;
    border-color: #b9d6f5 !important;
    color: #245c8f !important;
    -webkit-text-fill-color: #245c8f !important;
}

.st-key-mypage-shell [class*="st-key-mypage-download-"] button:disabled {
    background: #f4f8fc !important;
    border-color: #d7e2ea !important;
    color: #8a98a4 !important;
    -webkit-text-fill-color: #8a98a4 !important;
    opacity: 0.65;
}

.st-key-mypage-shell [class*="st-key-mypage-original-"] a p,
.st-key-mypage-shell [class*="st-key-mypage-original-"] button p,
.st-key-mypage-shell [class*="st-key-mypage-download-"] a p,
.st-key-mypage-shell [class*="st-key-mypage-download-"] button p {
    margin: 0;
    line-height: 1 !important;
}
"""
