from frontend.css.mypage_parts.navigation_actions import MYPAGE_NAVIGATION_ACTIONS_CSS

MYPAGE_NAVIGATION_BASE_CSS = """
.mypage-nav-label {
    margin: 22px 0 8px;
    color: #8a918e;
    font-size: 13px;
    font-weight: 700;
}

.st-key-mypage-shell [data-testid="column"]:has(.mypage-sidebar-head) button,
.st-key-mypage-shell [data-testid="stColumn"]:has(.mypage-sidebar-head)
    div[data-testid="stButton"]
    button,
.st-key-mypage-shell [data-testid="stColumn"]:has(.mypage-sidebar-head)
    div[data-testid="stFormSubmitButton"]
    button,
.st-key-mypage-shell [data-testid="stColumn"]:has(.mypage-sidebar-head) button,
.st-key-mypage-shell [data-testid="stColumn"]:has(.mypage-sidebar-head) button:hover,
.st-key-mypage-shell [data-testid="stColumn"]:has(.mypage-sidebar-head) button:focus,
.st-key-mypage-shell [data-testid="stColumn"]:has(.mypage-sidebar-head) button:active {
    border: 0 !important;
    border-width: 0 !important;
    border-color: transparent !important;
    outline: 0 !important;
    box-shadow: none !important;
    background: #ffffff !important;
    background-color: #ffffff !important;
    font-size: 19.2px !important;
}

.st-key-mypage-shell [data-testid="stColumn"]:has(.mypage-sidebar-head) button p,
.st-key-mypage-shell [data-testid="stColumn"]:has(.mypage-sidebar-head)
    button
    div[data-testid="stMarkdownContainer"] {
    color: #202725 !important;
    -webkit-text-fill-color: #202725 !important;
    font-size: 19.2px !important;
}

.st-key-mypage-shell [data-testid="stColumn"]:has(.mypage-sidebar-head) button::before,
.st-key-mypage-shell [data-testid="stColumn"]:has(.mypage-sidebar-head) button::after {
    border: 0 !important;
    border-width: 0 !important;
    box-shadow: none !important;
}

div[data-testid="stElementContainer"]:has(.mypage-sidebar-button-marker) {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

div[data-testid="stElementContainer"]:has(.mypage-sidebar-button-marker)
    + div[data-testid="stButton"]
    button,
div[data-testid="stElementContainer"]:has(.mypage-sidebar-button-marker)
    + div[data-testid="stButton"]
    button:hover,
div[data-testid="stElementContainer"]:has(.mypage-sidebar-button-marker)
    + div[data-testid="stButton"]
    button:focus,
div[data-testid="stElementContainer"]:has(.mypage-sidebar-button-marker)
    + div[data-testid="stButton"]
    button:active,
div[data-testid="stElementContainer"]:has(.mypage-sidebar-button-marker)
    + div[data-testid="stFormSubmitButton"]
    button,
div[data-testid="stElementContainer"]:has(.mypage-sidebar-button-marker)
    + div[data-testid="stFormSubmitButton"]
    button:hover,
div[data-testid="stElementContainer"]:has(.mypage-sidebar-button-marker)
    + div[data-testid="stFormSubmitButton"]
    button:focus,
div[data-testid="stElementContainer"]:has(.mypage-sidebar-button-marker)
    + div[data-testid="stFormSubmitButton"]
    button:active {
    border: 0 !important;
    border-width: 0 !important;
    border-color: transparent !important;
    outline: 0 !important;
    box-shadow: none !important;
    background: #ffffff !important;
    background-color: #ffffff !important;
    color: #202725 !important;
    -webkit-text-fill-color: #202725 !important;
}

div[data-testid="stElementContainer"]:has(.mypage-sidebar-button-marker)
    + div[data-testid="stButton"]
    button *,
div[data-testid="stElementContainer"]:has(.mypage-sidebar-button-marker)
    + div[data-testid="stFormSubmitButton"]
    button * {
    color: #202725 !important;
    -webkit-text-fill-color: #202725 !important;
}

.st-key-mypage-nav-recent button,
.st-key-mypage-nav-recent button:hover,
.st-key-mypage-nav-recent button:focus,
.st-key-mypage-nav-recent button:active,
.st-key-mypage-folder-none button,
.st-key-mypage-folder-none button:hover,
.st-key-mypage-folder-none button:focus,
.st-key-mypage-folder-none button:active,
.st-key-mypage-nav-uploads button,
.st-key-mypage-nav-uploads button:hover,
.st-key-mypage-nav-uploads button:focus,
.st-key-mypage-nav-uploads button:active,
.st-key-mypage-nav-account button,
.st-key-mypage-nav-account button:hover,
.st-key-mypage-nav-account button:focus,
.st-key-mypage-nav-account button:active,
[class*="st-key-mypage-folder-"] button,
[class*="st-key-mypage-folder-"] button:hover,
[class*="st-key-mypage-folder-"] button:focus,
[class*="st-key-mypage-folder-"] button:active {
    justify-content: flex-start;
    border: 0 !important;
    border-width: 0 !important;
    border-color: transparent !important;
    border-radius: 8px !important;
    outline: 0 !important;
    box-shadow: none !important;
    background: #ffffff !important;
    background-color: #ffffff !important;
    color: #202725 !important;
    -webkit-text-fill-color: #202725 !important;
    font-weight: 700 !important;
}
"""

MYPAGE_NAVIGATION_CSS = "\n".join(
    (
        MYPAGE_NAVIGATION_BASE_CSS.strip(),
        MYPAGE_NAVIGATION_ACTIONS_CSS.strip(),
    )
)
