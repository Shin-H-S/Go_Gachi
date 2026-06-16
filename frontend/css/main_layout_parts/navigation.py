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
"""
