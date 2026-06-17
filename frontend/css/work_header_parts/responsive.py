WORK_HEADER_RESPONSIVE_CSS = """
@media (max-width: 900px) {
    .block-container:has(.work-profile-card),
    .block-container:has(.work-auth),
    div[data-testid="stMainBlockContainer"]:has(.work-profile-card),
    div[data-testid="stMainBlockContainer"]:has(.work-auth) {
        padding-top: 9px !important;
    }

    .st-key-work-hero {
        margin-bottom: 24px;
    }
}
"""
