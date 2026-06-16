MYPAGE_NAVIGATION_ACTIONS_CSS = """
.st-key-mypage-new-work button,
.st-key-mypage-new-work-simple button {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 60% !important;
    min-width: 184px;
    min-height: 56px !important;
    margin-left: auto;
    border-radius: 999px !important;
    border: 0 !important;
    background: #173d14 !important;
    background-color: #173d14 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 15px !important;
    font-weight: 950 !important;
    box-shadow: none !important;
}

.st-key-mypage-new-work button:hover,
.st-key-mypage-new-work-simple button:hover {
    background: #173d14 !important;
    background-color: #173d14 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

.st-key-mypage-new-work button:not(:hover),
.st-key-mypage-new-work-simple button:not(:hover) {
    background: #173d14 !important;
    background-color: #173d14 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border-color: #173d14 !important;
}

.st-key-mypage-new-work button *,
.st-key-mypage-new-work-simple button * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

.st-key-mypage-settings-control,
.st-key-mypage-new-folder-control {
    width: 44px !important;
    height: 44px !important;
}

.st-key-mypage-new-folder-control {
    position: relative;
    margin: 14px auto 0 !important;
}

.st-key-mypage-settings-control
    div[data-testid="stElementContainer"]:has(.mypage-icon-button-visual),
.st-key-mypage-new-folder-control
    div[data-testid="stElementContainer"]:has(.mypage-icon-button-visual) {
    display: block !important;
    position: absolute !important;
    inset: 0 !important;
    width: 44px !important;
    height: 44px !important;
    margin: 0 !important;
    padding: 0 !important;
    pointer-events: none !important;
    z-index: 3;
}

.mypage-icon-button-visual,
.mypage-icon-button-visual img {
    display: block;
    width: 44px !important;
    height: 44px !important;
}

.mypage-icon-button-visual {
    pointer-events: none;
}

.mypage-icon-button-visual img {
    object-fit: contain;
}

.st-key-mypage-settings-control div[data-testid="stButton"],
.st-key-mypage-new-folder-control div[data-testid="stButton"] {
    position: absolute !important;
    inset: 0 !important;
    width: 44px !important;
    height: 44px !important;
    margin: 0 !important;
    z-index: 2;
}

.st-key-mypage-settings-control button,
.st-key-mypage-settings-control button:hover,
.st-key-mypage-settings-control button:focus,
.st-key-mypage-settings-control button:active,
.st-key-mypage-new-folder-control button,
.st-key-mypage-new-folder-control button:hover,
.st-key-mypage-new-folder-control button:focus,
.st-key-mypage-new-folder-control button:active {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border: 0 !important;
    border-width: 0 !important;
    border-color: transparent !important;
    border-radius: 8px !important;
    outline: 0 !important;
    box-shadow: none !important;
    background: transparent !important;
    background-color: transparent !important;
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
    width: 44px !important;
    height: 44px !important;
    min-height: 44px !important;
    padding: 0 !important;
    font-size: 0 !important;
    line-height: 0 !important;
}

.st-key-mypage-settings-control button *,
.st-key-mypage-new-folder-control button * {
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
    font-size: 0 !important;
    line-height: 0 !important;
}

[class*="st-key-mypage-folder-row-"] {
    margin: 0 !important;
}

.st-key-mypage-shell [class*="st-key-mypage-folder-menu-"] button,
.st-key-mypage-shell [class*="st-key-mypage-folder-menu-"] button:hover,
.st-key-mypage-shell [class*="st-key-mypage-folder-menu-"] button:focus,
.st-key-mypage-shell [class*="st-key-mypage-folder-menu-"] button:active {
    justify-content: center !important;
    min-width: 36px !important;
    min-height: 36px !important;
    padding: 0 !important;
    border-radius: 8px !important;
    font-size: 20px !important;
    font-weight: 900 !important;
}

.st-key-mypage-shell [class*="st-key-mypage-delete-folder-confirm-"] {
    margin: 6px 0 10px;
}

"""
