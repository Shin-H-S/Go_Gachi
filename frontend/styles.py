import streamlit as st

from frontend.css.base import BASE_CSS
from frontend.css.login import LOGIN_CSS
from frontend.css.main_layout import MAIN_LAYOUT_CSS
from frontend.css.main_visual import MAIN_VISUAL_CSS
from frontend.css.mypage import MYPAGE_CSS
from frontend.css.responsive import RESPONSIVE_CSS
from frontend.css.signup import SIGNUP_CSS
from frontend.css.work_channels import WORK_CHANNELS_CSS
from frontend.css.work_controls import WORK_CONTROLS_CSS
from frontend.css.work_forms import WORK_FORMS_CSS
from frontend.css.work_header import WORK_HEADER_CSS
from frontend.css.work_loading import WORK_LOADING_CSS
from frontend.css.work_preview import WORK_PREVIEW_CSS
from frontend.css.work_selection import WORK_SELECTION_CSS
from frontend.css.work_upload import WORK_UPLOAD_CSS

CSS_PARTS = [
    BASE_CSS,
    LOGIN_CSS,
    MAIN_LAYOUT_CSS,
    MAIN_VISUAL_CSS,
    SIGNUP_CSS,
    WORK_FORMS_CSS,
    WORK_PREVIEW_CSS,
    WORK_LOADING_CSS,
    WORK_CONTROLS_CSS,
    WORK_HEADER_CSS,
    WORK_UPLOAD_CSS,
    WORK_CHANNELS_CSS,
    WORK_SELECTION_CSS,
    MYPAGE_CSS,
    RESPONSIVE_CSS,
]


def build_css() -> str:
    return "\n".join(part.strip("\n") for part in CSS_PARTS)


def add_css() -> None:
    st.markdown(f"<style>\n{build_css()}\n</style>", unsafe_allow_html=True)
