WORK_HEADER_PROFILE_CSS = """
.block-container:has(.work-profile-card),
.block-container:has(.work-auth),
div[data-testid="stMainBlockContainer"]:has(.work-profile-card),
div[data-testid="stMainBlockContainer"]:has(.work-auth) {
    padding-top: 12px !important;
    padding-bottom: 0 !important;
    margin-bottom: calc(var(--work-generate-button-height, 60px) * -0.55);
}

.st-key-work-hero {
    margin: 0 0 20px;
    padding: 0;
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}

.work-profile-card {
    position: relative;
    z-index: 2;
    display: inline-flex;
    align-items: center;
    gap: 12px;
    min-height: 58px;
    width: 100%;
    cursor: pointer;
    pointer-events: none;
}

.work-profile-avatar {
    width: 44px;
    height: 44px;
    flex: 0 0 44px;
    display: inline-grid;
    place-items: center;
    border-radius: 999px;
    background: #202725;
    color: #ffffff;
    font-size: 18px;
    font-weight: 950;
    line-height: 1;
}

.work-profile-text {
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 3px;
}

.work-profile-text strong {
    color: #0f1715;
    font-size: 18px;
    font-weight: 950;
    line-height: 1.15;
    white-space: nowrap;
}

.work-profile-text small {
    color: #5f8580;
    font-size: 12px;
    font-weight: 650;
    line-height: 1.2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.st-key-work-mypage-link {
    position: relative;
    z-index: 1;
    margin-top: -58px;
}

.st-key-work-mypage-link button,
.st-key-work-mypage-link button[data-testid="stBaseButton-secondary"],
.st-key-work-mypage-link button[kind="secondary"] {
    min-height: 58px !important;
    border: 0 !important;
    border-color: transparent !important;
    border-radius: 0 !important;
    background: transparent !important;
    background-color: transparent !important;
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
    padding: 0 !important;
    box-shadow: none !important;
    outline: 0 !important;
}

.st-key-work-mypage-link button:hover,
.st-key-work-mypage-link button:focus,
.st-key-work-mypage-link button:active {
    border: 0 !important;
    border-color: transparent !important;
    background: transparent !important;
    background-color: transparent !important;
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
    box-shadow: none !important;
    outline: 0 !important;
}

.st-key-work-mypage-link button::before,
.st-key-work-mypage-link button::after {
    border: 0 !important;
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
}

.st-key-work-mypage-link button p,
.st-key-work-mypage-link button div[data-testid="stMarkdownContainer"] {
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
}
"""
