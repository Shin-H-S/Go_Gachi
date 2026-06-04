LOGIN_CSS = """
.main .block-container:has(.st-key-login-page) {
    max-width: none;
    padding: 0;
}

.st-key-login-page {
    min-height: 100vh;
    background: #ffffff;
    color: #0b0e14;
    overflow: hidden;
}

.st-key-login-page [data-testid="stHorizontalBlock"] {
    gap: 0 !important;
    align-items: stretch;
}

.st-key-login-page [data-testid="column"] {
    min-height: 100vh;
    padding: 0 !important;
}

.st-key-login-page [data-testid="column"]:has(.login-brand) {
    background: #ffffff;
}

.st-key-login-page [data-testid="column"]:has(.login-blue-panel) {
    background: #2563c7;
}

.login-brand {
    display: inline-flex;
    align-items: center;
    margin: 54px 0 44px 46px;
    color: #0b0e14 !important;
    -webkit-text-fill-color: #0b0e14 !important;
    font-size: 44px;
    font-weight: 950;
    line-height: 1;
    text-decoration: none !important;
}

.login-brand span {
    color: #3fd765;
    -webkit-text-fill-color: #3fd765;
    margin-left: 3px;
    font-size: 52px;
    line-height: 0.8;
}

.login-heading {
    width: min(620px, calc(100vw - 56px));
    margin: 30px auto 30px;
    text-align: center;
}

.login-heading h1 {
    margin: 0;
    color: #050607;
    font-size: 40px;
    font-weight: 950;
    line-height: 1.12;
}

.login-heading p {
    margin: 24px 0 0;
    color: #526579;
    font-size: 20px;
    font-weight: 650;
    line-height: 1.45;
}

.st-key-login-page div[data-testid="stAlert"] {
    width: min(620px, calc(100vw - 56px));
    margin: 0 auto 18px;
}

.st-key-login-page div[data-testid="stForm"]:has(.login-form-fields-marker) {
    width: min(620px, calc(100vw - 56px));
    margin: 56px auto 0;
    padding: 0;
    border: 0;
    background: transparent;
}

.st-key-login-page div[data-testid="stForm"]:has(.login-form-fields-marker) label {
    color: #263647 !important;
    font-size: 15px !important;
    font-weight: 800 !important;
}

.st-key-login-page div[data-testid="stForm"]:has(.login-form-fields-marker) input {
    min-height: 62px;
    border: 0 !important;
    border-radius: 8px !important;
    background: #f2f3f1 !important;
    color: #1f2d3d !important;
    font-size: 18px !important;
    font-weight: 650 !important;
}

.st-key-login-page div[data-testid="stForm"]:has(.login-form-fields-marker) input:focus {
    box-shadow: inset 0 0 0 2px #2563c7 !important;
}

.st-key-login-page div[data-testid="stForm"]:has(.login-form-fields-marker)
    div[data-testid="stFormSubmitButton"] {
    margin-top: 16px;
}

.st-key-login-page div[data-testid="stForm"]:has(.login-form-fields-marker)
    div[data-testid="stFormSubmitButton"] button {
    min-height: 62px !important;
    border: 0 !important;
    border-radius: 8px !important;
    background: #050607 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 20px !important;
    font-weight: 950 !important;
    box-shadow: none !important;
}

.st-key-login-page div[data-testid="stForm"]:has(.login-form-fields-marker)
    div[data-testid="stFormSubmitButton"] button:hover {
    background: #1d2430 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

.login-links {
    width: min(620px, calc(100vw - 56px));
    margin: 34px auto 0;
    text-align: center;
}

.login-links a {
    color: #4b22ff !important;
    -webkit-text-fill-color: #4b22ff !important;
    font-size: 17px;
    font-weight: 800;
    text-decoration: none !important;
}

.login-links a:hover {
    text-decoration: underline !important;
}

.login-links p {
    margin: 30px 0 0;
    color: #263647;
    font-size: 16px;
    font-weight: 650;
}

.login-blue-panel {
    min-height: 100vh;
    width: 100%;
    background: #2563c7;
}

@media (max-width: 900px) {
    .st-key-login-page [data-testid="stHorizontalBlock"] {
        display: block !important;
    }

    .st-key-login-page [data-testid="column"] {
        min-height: auto;
    }

    .login-brand {
        margin: 30px 0 34px 24px;
        font-size: 34px;
    }

    .login-brand span {
        font-size: 42px;
    }

    .login-heading {
        margin-top: 18px;
    }

    .login-heading h1 {
        font-size: 32px;
    }

    .st-key-login-page div[data-testid="stForm"]:has(.login-form-fields-marker) {
        margin-top: 36px;
    }

    .login-blue-panel {
        min-height: 180px;
        margin-top: 38px;
    }
}
"""
