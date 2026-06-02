import streamlit as st
from style_base import BASE_CSS
from style_main_layout import MAIN_LAYOUT_CSS
from style_main_visual import MAIN_VISUAL_CSS
from style_responsive import RESPONSIVE_CSS
from style_work_channels import WORK_CHANNELS_CSS
from style_work_controls import WORK_CONTROLS_CSS
from style_work_forms import WORK_FORMS_CSS
from style_work_preview import WORK_PREVIEW_CSS
from style_work_selection import WORK_SELECTION_CSS
from style_work_upload import WORK_UPLOAD_CSS

CSS_PARTS = [
    BASE_CSS,
    MAIN_LAYOUT_CSS,
    MAIN_VISUAL_CSS,
    WORK_FORMS_CSS,
    WORK_PREVIEW_CSS,
    WORK_CONTROLS_CSS,
    WORK_UPLOAD_CSS,
    WORK_CHANNELS_CSS,
    WORK_SELECTION_CSS,
    RESPONSIVE_CSS,
]


def build_css() -> str:
    return "\n".join(part.strip("\n") for part in CSS_PARTS)


def add_css() -> None:
    st.markdown(f"<style>\n{build_css()}\n</style>", unsafe_allow_html=True)
