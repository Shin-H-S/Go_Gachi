from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import httpx
import streamlit as st

from frontend.services.api_client import request_asset_bytes, to_backend_asset_url

DOWNLOAD_LABEL = "⇩ 다운로드"


@st.cache_data(show_spinner=False)
def _cached_asset_bytes(url: str) -> bytes:
    return request_asset_bytes(url)


def _download_file_name(item: dict) -> str:
    request_id = str(item.get("request_id") or "").strip()
    suffix = request_id.replace("/", "-").replace("\\", "-") or "image"
    return f"go_gachi_ad_{suffix}.png"


def _download_url_for_item(item: dict) -> str | None:
    return to_backend_asset_url(item.get("download_url")) or to_backend_asset_url(
        item.get("image_url")
    )


def _download_payload(items: list[dict]) -> tuple[bytes, str, str, bool]:
    downloadable = []
    for item in items:
        download_url = _download_url_for_item(item)
        if download_url:
            downloadable.append((item, download_url))
    if not downloadable:
        return b"", "go_gachi_ad_image.png", "image/png", True
    if len(downloadable) == 1:
        item, image_url = downloadable[0]
        return _cached_asset_bytes(str(image_url)), _download_file_name(item), "image/png", False

    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        for item, image_url in downloadable:
            archive.writestr(_download_file_name(item), _cached_asset_bytes(str(image_url)))
    return buffer.getvalue(), "go_gachi_selected_images.zip", "application/zip", False


def render_download_action(selected_items: list[dict], *, enabled: bool) -> None:
    if not enabled:
        st.button(
            DOWNLOAD_LABEL,
            key="mypage-action-download",
            disabled=True,
            use_container_width=True,
        )
        return

    if len(selected_items) == 1:
        download_url = _download_url_for_item(selected_items[0])
        if download_url:
            st.link_button(
                DOWNLOAD_LABEL,
                download_url,
                key="mypage-action-download",
                use_container_width=True,
            )
            return
        st.button(
            DOWNLOAD_LABEL,
            key="mypage-action-download",
            disabled=True,
            use_container_width=True,
        )
        return

    data, file_name, mime, disabled = b"", "go_gachi_ad_image.png", "image/png", not enabled
    try:
        data, file_name, mime, disabled = _download_payload(selected_items)
    except httpx.HTTPError:
        disabled = True
    st.download_button(
        DOWNLOAD_LABEL,
        data=data,
        file_name=file_name,
        mime=mime,
        key="mypage-action-download",
        disabled=disabled,
        use_container_width=True,
    )
