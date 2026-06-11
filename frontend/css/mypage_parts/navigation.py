MYPAGE_NAVIGATION_CSS = """
.mypage-nav-label {
    margin: 22px 0 8px;
    color: #8a918e;
    font-size: 13px;
    font-weight: 700;
}

.st-key-mypage-nav-recent button,
.st-key-mypage-folder-none button,
.st-key-mypage-nav-uploads button,
.st-key-mypage-nav-account button,
[class*="st-key-mypage-folder-"] button {
    justify-content: flex-start;
    border: 0 !important;
    border-radius: 8px !important;
    background: transparent !important;
    color: #202725 !important;
    font-weight: 700 !important;
}

.st-key-mypage-new-work button,
.st-key-mypage-new-work-simple button {
    border-radius: 8px !important;
    border: 0 !important;
    background: #0f8f7f !important;
    color: #ffffff !important;
    font-weight: 800 !important;
}

.st-key-mypage-new-folder button {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    border: 0 !important;
    border-radius: 8px !important;
    background: #edf0ed !important;
    color: #18211f !important;
    font-weight: 800 !important;
}

.st-key-mypage-new-folder button div[data-testid="stMarkdownContainer"],
.st-key-mypage-new-folder button p {
    flex: 0 0 auto !important;
    width: auto !important;
    max-width: max-content !important;
    margin: 0 !important;
    text-align: left !important;
}

.st-key-mypage-new-folder button::before {
    content: "+";
    width: 18px;
    height: 18px;
    display: inline-grid;
    place-items: center;
    margin-right: 0;
    flex: 0 0 auto;
    border-radius: 999px;
    border: 1px solid rgba(24, 33, 31, 0.18);
    background: #ffffff;
    color: #18211f;
    font: 900 14px/1 sans-serif;
}
"""
