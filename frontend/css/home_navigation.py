from frontend.home_button import home_icon_data_url, work_icon_data_url

HOME_NAVIGATION_CSS = """
.st-key-work-main-link-control,
.st-key-mypage-main-link-control,
.st-key-mypage-work-link-control {
    position: relative !important;
    display: flex !important;
    align-items: center !important;
    width: 52px !important;
    min-width: 52px;
    z-index: 1000001 !important;
}

.st-key-work-main-link-control {
    justify-content: flex-start !important;
    min-height: 58px !important;
    padding-top: 3px !important;
}

.st-key-mypage-main-link-control,
.st-key-mypage-work-link-control {
    justify-content: flex-end !important;
    min-height: 56px !important;
}

.st-key-work-main-link-control div[data-testid="stButton"],
.st-key-mypage-main-link-control div[data-testid="stButton"],
.st-key-mypage-work-link-control div[data-testid="stButton"] {
    width: 52px !important;
    height: 52px !important;
    margin: 0 !important;
    padding: 0 !important;
}

.st-key-work-main-link-control button,
.st-key-work-main-link-control button[kind="secondary"],
.st-key-work-main-link-control button:hover,
.st-key-work-main-link-control button:focus,
.st-key-work-main-link-control button:active,
.st-key-mypage-main-link-control button,
.st-key-mypage-main-link-control button[kind="secondary"],
.st-key-mypage-main-link-control button:hover,
.st-key-mypage-main-link-control button:focus,
.st-key-mypage-main-link-control button:active {
    display: inline-flex !important;
    position: relative !important;
    align-items: center !important;
    justify-content: center !important;
    width: 52px !important;
    min-width: 52px;
    height: 52px !important;
    min-height: 52px !important;
    padding: 0 !important;
    border: 0 !important;
    border-width: 0 !important;
    border-color: transparent !important;
    border-radius: 999px !important;
    outline: 0 !important;
    background-color: #ffffff !important;
    background-image: url("__HOME_ICON_SRC__") !important;
    background-position: center !important;
    background-repeat: no-repeat !important;
    background-size: 32px 32px !important;
    box-shadow: none !important;
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
    font-size: 0 !important;
    line-height: 0 !important;
    z-index: 1000001 !important;
}

.st-key-mypage-work-link-control button,
.st-key-mypage-work-link-control button[kind="secondary"],
.st-key-mypage-work-link-control button:hover,
.st-key-mypage-work-link-control button:focus,
.st-key-mypage-work-link-control button:active {
    display: inline-flex !important;
    position: relative !important;
    align-items: center !important;
    justify-content: center !important;
    width: 52px !important;
    min-width: 52px;
    height: 52px !important;
    min-height: 52px !important;
    padding: 0 !important;
    border: 0 !important;
    border-width: 0 !important;
    border-color: transparent !important;
    border-radius: 999px !important;
    outline: 0 !important;
    background-color: #ffffff !important;
    background-image: url("__WORK_ICON_SRC__") !important;
    background-position: center !important;
    background-repeat: no-repeat !important;
    background-size: 26px 26px !important;
    box-shadow: none !important;
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
    font-size: 0 !important;
    line-height: 0 !important;
    z-index: 1000001 !important;
}

.st-key-work-main-link-control button *,
.st-key-mypage-main-link-control button *,
.st-key-mypage-work-link-control button * {
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
    font-size: 0 !important;
    line-height: 0 !important;
}
""".replace("__HOME_ICON_SRC__", home_icon_data_url()).replace(
    "__WORK_ICON_SRC__",
    work_icon_data_url(),
)
