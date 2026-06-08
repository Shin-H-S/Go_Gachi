import base64
from io import BytesIO
from types import SimpleNamespace

from PIL import Image


def test_frontend_config_exposes_preset_helpers() -> None:
    from frontend.config import (
        CHANNEL_SLUGS,
        FORMAT_OPTIONS,
        format_size_label,
        get_detail_id,
        get_detail_size,
    )

    format_label = next(
        label for label, option in FORMAT_OPTIONS.items() if option["value"] == "instagram"
    )
    detail_label = next(
        detail["label"]
        for detail in FORMAT_OPTIONS[format_label]["details"]
        if detail["id"] == "square_feed"
    )

    assert FORMAT_OPTIONS[format_label]["value"] == "instagram"
    assert CHANNEL_SLUGS[format_label] == "instagram"
    assert get_detail_id(format_label, str(detail_label)) == "square_feed"
    assert get_detail_size(format_label, str(detail_label)) == (1080, 1080)
    assert format_size_label((1080, 1080)) == "1080 x 1080"


def test_frontend_config_can_load_presets_from_backend(monkeypatch) -> None:
    from frontend import config

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, list[dict[str, object]]]:
            return {
                "presets": [
                    {
                        "id": "custom_channel",
                        "label": "Custom Channel",
                        "width": 100,
                        "height": 200,
                        "details": [
                            {
                                "id": "custom_detail",
                                "label": "Custom Detail",
                                "width": 300,
                                "height": 400,
                            }
                        ],
                    }
                ]
            }

    def fake_get(url: str, timeout: int) -> FakeResponse:
        assert url == f"{config.BACKEND_URL}/api/config"
        assert timeout == 2
        return FakeResponse()

    monkeypatch.setattr(config.httpx, "get", fake_get)

    options = config._format_options_from_presets(config._load_backend_presets())

    assert options["Custom Channel"]["value"] == "custom_channel"
    assert options["Custom Channel"]["details"][0]["id"] == "custom_detail"
    assert options["Custom Channel"]["details"][0]["size"] == (300, 400)


def test_frontend_config_falls_back_to_local_presets(monkeypatch) -> None:
    from frontend import config

    def fake_get(*args, **kwargs):  # noqa: ANN002, ANN003
        raise config.httpx.ConnectError("backend down")

    monkeypatch.setattr(config, "FRONTEND_CONFIG_SOURCE", "auto")
    monkeypatch.setattr(config, "FRONTEND_USE_MOCK", False)
    monkeypatch.setattr(config.httpx, "get", fake_get)

    presets = config.load_presets()

    assert presets[0]["id"] == "instagram"


def test_image_utils_builds_preview_canvas_and_data_url() -> None:
    from frontend.image_utils import bytes_to_data_url, make_preview_canvas

    source = BytesIO()
    Image.new("RGB", (8, 4), "#225544").save(source, format="PNG")

    format_label, detail_label = _instagram_square_labels()
    preview_bytes = make_preview_canvas(source.getvalue(), format_label, detail_label)
    preview = Image.open(BytesIO(preview_bytes))

    assert preview.size == (1080, 1080)
    assert bytes_to_data_url(b"abc") == "data:image/png;base64,YWJj"


def test_api_client_converts_uploads_and_feedback() -> None:
    from frontend.api_client import build_feedback, data_url_to_bytes, file_to_data_url

    uploaded_file = SimpleNamespace(type="image/png", getvalue=lambda: b"image-bytes")
    data_url = file_to_data_url(uploaded_file)

    assert data_url == _data_url(b"image-bytes")
    assert data_url_to_bytes(data_url) == b"image-bytes"
    assert build_feedback("  show it bigger  ", "Square feed") == (
        "광고 유형: Square feed\nshow it bigger"
    )


def _data_url(payload: bytes) -> str:
    return f"data:image/png;base64,{base64.b64encode(payload).decode('ascii')}"


def _instagram_square_labels() -> tuple[str, str]:
    from frontend.config import FORMAT_OPTIONS

    format_label = next(
        label for label, option in FORMAT_OPTIONS.items() if option["value"] == "instagram"
    )
    detail_label = next(
        str(detail["label"])
        for detail in FORMAT_OPTIONS[format_label]["details"]
        if detail["id"] == "square_feed"
    )
    return format_label, detail_label
