MAIN_LAYOUT_CSS = """
.st-key-main-landing {
    min-height: 100vh;
    min-height: 100dvh;
    padding: 34px;
    border-radius: 0;
    background: #d8ff00;
    color: #193511;
    overflow: hidden;
    box-sizing: border-box;
}

.stApp:has(.st-key-main-landing),
[data-testid="stAppViewContainer"]:has(.st-key-main-landing),
[data-testid="stMain"]:has(.st-key-main-landing),
[data-testid="stMainBlockContainer"]:has(.st-key-main-landing) {
    background: #d8ff00 !important;
}

.main .block-container:has(.st-key-main-landing) {
    max-width: none;
    min-height: 100vh;
    min-height: 100dvh;
    padding: 0;
    background: #d8ff00;
}

.st-key-main-landing > div {
    max-width: 1720px;
    margin: 0 auto;
}

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

.st-key-main-landing [data-testid="stHorizontalBlock"] {
    align-items: center;
}

.main-landing {
    padding-top: 150px;
}

.hero-kicker {
    display: inline-flex;
    align-items: center;
    min-height: 32px;
    padding: 0 12px;
    border: 1px solid rgba(25, 53, 17, 0.28);
    border-radius: 999px;
    color: #193511;
    background: rgba(255, 255, 255, 0.32);
    font-size: 13px;
    font-weight: 950;
    margin: 0 0 22px;
}

.hero-title {
    color: #24461d;
    font-size: 86px;
    line-height: 0.98;
    font-weight: 950;
    margin: 0;
}

.hero-copy {
    max-width: 760px;
    color: #24461d;
    font-size: 23px;
    line-height: 1.48;
    font-weight: 700;
    margin: 30px 0 48px;
    word-break: keep-all;
}

.landing-start-link {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 80px;
    width: min(380px, 100%);
    border: 0;
    border-radius: 999px;
    background: #24551e;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 21px;
    font-weight: 950;
    text-decoration: none !important;
    box-shadow: 0 18px 34px rgba(36, 85, 30, 0.28);
    box-sizing: border-box;
}

.landing-start-link:hover {
    background: #173d14;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    text-decoration: none !important;
    transform: translateY(-1px);
}

div[data-testid="stElementContainer"]:has(.main-start-button-marker)
    + div[data-testid="stButton"] button {
    min-height: 80px !important;
    border: 0 !important;
    border-radius: 999px !important;
    background: #24551e !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 21px !important;
    font-weight: 950 !important;
    box-shadow: 0 18px 34px rgba(36, 85, 30, 0.28) !important;
}

div[data-testid="stElementContainer"]:has(.main-start-button-marker)
    + div[data-testid="stButton"] button:hover {
    background: #173d14 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    transform: translateY(-1px);
}
"""
