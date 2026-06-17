MAIN_LAYOUT_NAVIGATION_CSS = """
.landing-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 28px;
    width: 100%;
    min-height: 96px;
    padding: 14px 18px 14px 42px;
    border-radius: 999px;
    background: #ffffff;
    box-shadow: 0 18px 36px rgba(25, 53, 17, 0.12);
    box-sizing: border-box;
}

.landing-brand {
    color: #0b0e14;
    font-size: 33px;
    font-weight: 950;
    line-height: 1;
    white-space: nowrap;
}

.landing-brand span {
    color: #0b0e14;
    margin-left: 2px;
}

.landing-auth {
    display: flex;
    align-items: center;
    gap: 10px;
    color: #0b0e14;
    font-size: 18px;
    font-weight: 900;
    white-space: nowrap;
}

.landing-auth-logout-slot {
    min-width: 148px;
    min-height: 78px;
}

.landing-login,
.landing-signup {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 78px;
    padding: 0 34px;
    border-radius: 8px;
    box-sizing: border-box;
    text-decoration: none !important;
}

.landing-login {
    background: #eff1ec;
    color: #0b0e14 !important;
    -webkit-text-fill-color: #0b0e14 !important;
}

.landing-signup {
    border-radius: 999px;
    background: #1e2433;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

.landing-login:hover,
.landing-login:visited {
    color: #0b0e14 !important;
    -webkit-text-fill-color: #0b0e14 !important;
    text-decoration: none !important;
}

.landing-signup:hover,
.landing-signup:visited {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    text-decoration: none !important;
}

.st-key-main-logout-button {
    position: absolute !important;
    top: 48px;
    right: 52px;
    z-index: 10;
    transform: translateX(-100%);
    width: auto !important;
    margin: 0 !important;
}

.st-key-main-logout-button > div,
.st-key-main-logout-button div[data-testid="stButton"] {
    margin: 0 !important;
    width: auto !important;
}

.st-key-main-logout-button button {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-height: 78px !important;
    padding: 0 34px !important;
    border: 0 !important;
    border-color: transparent !important;
    border-radius: 8px !important;
    background: #eff1ec !important;
    background-color: #eff1ec !important;
    background-image: none !important;
    color: #0b0e14 !important;
    -webkit-text-fill-color: #0b0e14 !important;
    font-size: 18px !important;
    font-weight: 900 !important;
    line-height: 1 !important;
    box-shadow: none !important;
    outline: none !important;
    text-decoration: none !important;
    transform: none !important;
    transition: none !important;
    box-sizing: border-box !important;
}

.st-key-main-logout-button button:hover,
.st-key-main-logout-button button:focus,
.st-key-main-logout-button button:focus-visible,
.st-key-main-logout-button button:active {
    background: #eff1ec !important;
    background-color: #eff1ec !important;
    color: #0b0e14 !important;
    -webkit-text-fill-color: #0b0e14 !important;
    border: 0 !important;
    border-color: transparent !important;
    box-shadow: none !important;
    outline: none !important;
    transform: none !important;
    transition: none !important;
}

.st-key-main-logout-button button * {
    color: #0b0e14 !important;
    -webkit-text-fill-color: #0b0e14 !important;
    font-size: 18px !important;
    font-weight: 900 !important;
}

.st-key-main-logout-button div[data-testid="stButton"] button,
.st-key-main-logout-button div[data-testid="stButton"] button:hover,
.st-key-main-logout-button div[data-testid="stButton"] button:focus,
.st-key-main-logout-button div[data-testid="stButton"] button:focus-visible,
.st-key-main-logout-button div[data-testid="stButton"] button:active {
    border: 0 !important;
    border-color: transparent !important;
    background: #eff1ec !important;
    background-color: #eff1ec !important;
    background-image: none !important;
    color: #0b0e14 !important;
    -webkit-text-fill-color: #0b0e14 !important;
    box-shadow: none !important;
    outline: none !important;
    transform: none !important;
    transition: none !important;
}

.st-key-main-logout-button div[data-testid="stButton"] button p,
.st-key-main-logout-button div[data-testid="stButton"] button:hover p,
.st-key-main-logout-button div[data-testid="stButton"] button:focus p,
.st-key-main-logout-button div[data-testid="stButton"] button:focus-visible p,
.st-key-main-logout-button div[data-testid="stButton"] button:active p,
.st-key-main-logout-button div[data-testid="stButton"] button span,
.st-key-main-logout-button div[data-testid="stButton"] button:hover span,
.st-key-main-logout-button div[data-testid="stButton"] button:focus span,
.st-key-main-logout-button div[data-testid="stButton"] button:focus-visible span,
.st-key-main-logout-button div[data-testid="stButton"] button:active span {
    color: #0b0e14 !important;
    -webkit-text-fill-color: #0b0e14 !important;
    text-decoration: none !important;
    transition: none !important;
}
"""
