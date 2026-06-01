RESPONSIVE_CSS = """
@media (max-width: 900px) {
    .main .block-container {
        padding: 18px 14px 32px;
    }

    .main .block-container:has(.st-key-main-landing) {
        padding: 0;
    }

    .st-key-main-landing {
        min-height: 100vh;
        padding: 16px;
    }

    .landing-nav {
        min-height: auto;
        padding: 12px 12px 12px 18px;
        gap: 12px;
    }

    .landing-brand {
        font-size: 26px;
    }

    .landing-menu {
        display: none;
    }

    .landing-auth {
        gap: 6px;
        font-size: 14px;
    }

    .landing-login,
    .landing-signup {
        min-height: 52px;
        padding: 0 14px;
    }

    .main-landing {
        padding-top: 58px;
    }

    .hero-title {
        font-size: 52px;
        line-height: 1.03;
    }

    .hero-copy {
        font-size: 18px;
        line-height: 1.52;
        margin: 22px 0 30px;
    }

    .landing-url-chip,
    .landing-start-link,
    div[data-testid="stElementContainer"]:has(.main-start-button-marker)
        + div[data-testid="stButton"] button {
        min-height: 62px !important;
        font-size: 17px !important;
    }

    .hero-visual {
        --slide-height: 420px;
        padding-top: 34px;
    }

    .blue-slide-window,
    .blue-panel {
        min-height: 420px;
        border-radius: 28px;
    }

    .blue-panel {
        padding: 30px;
    }

    .blue-panel strong {
        font-size: 38px;
    }

    .preview-shell {
        height: 360px;
    }

}
"""
