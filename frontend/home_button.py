from functools import cache
from pathlib import Path

from frontend.media.image_data import bytes_to_data_url

HOME_BUTTON_LABEL = "홈"
HOME_BUTTON_HELP = "메인 페이지로 이동"
WORK_BUTTON_LABEL = "작업"
WORK_BUTTON_HELP = "작업 페이지로 이동"

_ASSET_DIR = Path(__file__).resolve().parent / "assets"
_HOME_ICON_PATH = _ASSET_DIR / "home.png"
_WORK_ICON_PATH = _ASSET_DIR / "work_page_icon.png"


@cache
def home_icon_data_url() -> str:
    return bytes_to_data_url(_HOME_ICON_PATH.read_bytes())


@cache
def work_icon_data_url() -> str:
    return bytes_to_data_url(_WORK_ICON_PATH.read_bytes())
