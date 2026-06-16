import streamlit as st

from frontend.core.config import format_size_label, get_detail_size
from frontend.media.image_data import bytes_to_data_url
from frontend.media.preview_canvas import make_preview_canvas


def compact_html(html: str) -> str:
    return " ".join(line.strip() for line in html.strip().splitlines() if line.strip())


def render_preview_shell(
    format_label: str,
    body_html: str,
    detail_label: str | None = None,
    summary_html: str = "",
) -> None:
    body = compact_html(body_html)
    summary = compact_html(summary_html) if summary_html else ""
    caption = f"{format_label} · {detail_label}" if detail_label else format_label
    size_label = (
        format_size_label(get_detail_size(format_label, detail_label)) if detail_label else ""
    )
    st.markdown(
        (
            '<div class="preview-shell">'
            '<div class="result-caption">'
            f"<span>{caption}</span>"
            f"<span>{size_label}</span>"
            "</div>"
            f"{summary}"
            f"{body}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_image_preview(
    image_bytes: bytes,
    format_label: str,
    detail_label: str | None = None,
    summary_html: str = "",
) -> None:
    preview_bytes = make_preview_canvas(image_bytes, format_label, detail_label)
    preview_src = bytes_to_data_url(preview_bytes)
    render_preview_shell(
        format_label,
        f"""
        <div class="preview-image-frame">
            <img src="{preview_src}" alt="미리보기 이미지" />
        </div>
        """,
        detail_label,
        summary_html,
    )


def render_image_url_preview(
    image_url: str,
    format_label: str,
    detail_label: str | None = None,
    summary_html: str = "",
) -> None:
    render_preview_shell(
        format_label,
        f"""
        <div class="preview-image-frame">
            <img src="{image_url}" alt="미리보기 이미지" />
        </div>
        """,
        detail_label,
        summary_html,
    )
