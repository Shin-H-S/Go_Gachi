import mimetypes
from collections.abc import MutableMapping
from pathlib import PurePosixPath
from urllib.parse import urlparse

from frontend.core.config import FORMAT_OPTIONS
from frontend.services.api_client import request_asset_bytes, to_backend_asset_url
from frontend.work.uploads import set_handoff_uploaded_file


def _channel_label_for_preset(preset_id: str) -> str | None:
    for label, option in FORMAT_OPTIONS.items():
        if str(option.get("value") or "") == preset_id:
            return label
    return None


def generation_work_image_url(item: dict) -> str | None:
    return to_backend_asset_url(item.get("image_url"))


def _mime_type_for_url(image_url: str) -> str:
    if image_url.startswith("data:"):
        header = image_url[5:].split(",", 1)[0]
        return header.split(";", 1)[0] or "application/octet-stream"

    return mimetypes.guess_type(urlparse(image_url).path)[0] or "image/png"


def _file_name_for_image(item: dict, image_url: str, mime_type: str) -> str:
    file_name = PurePosixPath(urlparse(image_url).path).name
    if file_name:
        return file_name

    request_id = str(item.get("request_id") or "selected-image").replace("/", "_")
    extension = mimetypes.guess_extension(mime_type) or ".png"
    return f"{request_id}{extension}"


def prepare_generation_for_work(
    session_state: MutableMapping[str, object],
    item: dict,
) -> bool:
    image_url = generation_work_image_url(item)
    if not image_url:
        return False

    image_bytes = request_asset_bytes(image_url)
    mime_type = _mime_type_for_url(image_url)
    set_handoff_uploaded_file(
        session_state,
        image_bytes=image_bytes,
        file_name=_file_name_for_image(item, image_url, mime_type),
        mime_type=mime_type,
    )

    session_state.pop("result_image_url", None)
    session_state.pop("result_bytes", None)
    session_state.pop("result_copy", None)
    session_state.pop("result_context", None)
    session_state["result_history"] = []
    session_state["result_cursor"] = 0
    session_state.pop("result_history_upload", None)

    channel_label = _channel_label_for_preset(str(item.get("preset_id") or ""))
    if channel_label:
        session_state["selected_channel"] = channel_label

    return True
