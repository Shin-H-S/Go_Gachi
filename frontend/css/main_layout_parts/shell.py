MAIN_LAYOUT_SHELL_CSS = """
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

.st-key-main-landing [data-testid="stHorizontalBlock"] {
    align-items: center;
}
"""
