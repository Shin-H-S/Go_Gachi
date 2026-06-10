import base64
import hashlib
from types import SimpleNamespace

from frontend import api_client
from frontend.work.copy import build_auto_copy
from frontend.work.state import build_result_context


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


def _labels_for_instagram_square() -> tuple[str, str]:
    format_label = next(
        label
        for label, option in api_client.FORMAT_OPTIONS.items()
        if option["value"] == "instagram"
    )
    detail_label = next(
        str(detail["label"])
        for detail in api_client.FORMAT_OPTIONS[format_label]["details"]
        if detail["id"] == "square_feed"
    )
    return format_label, detail_label


def _capture_generate_payload(monkeypatch, *, result_payload: dict[str, object] | None = None):
    captured_json: dict[str, object] = {}

    def fake_post(
        url: str,  # noqa: ARG001
        json: dict[str, object],
        headers: dict[str, str],  # noqa: ARG001
        timeout: int,  # noqa: ARG001
    ) -> FakeResponse:
        captured_json.update(json)
        return FakeResponse(result_payload or {"imageDataUrl": "data:image/png;base64,cmVzdWx0"})

    monkeypatch.setattr(api_client, "BACKEND_URL", "https://backend.example")
    monkeypatch.setattr(api_client.httpx, "post", fake_post)
    return captured_json


def test_1_text_overlay_disabled_skips_user_copy_and_forces_preserve_mode(
    monkeypatch,
) -> None:
    captured_json = _capture_generate_payload(monkeypatch)
    uploaded_file = SimpleNamespace(type="image/png", getvalue=lambda: b"source-image")
    format_label, detail_label = _labels_for_instagram_square()

    result = api_client.request_backend(
        uploaded_file,
        "제품은 크게 보여줘",
        format_label,
        detail_label,
        text_overlay_enabled=False,
        copy_mode="preserve",
        ad_copy_prompt="이미지에 들어가면 안 되는 문구",
    )

    assert result.image_bytes == b"result"
    assert captured_json["textOverlayEnabled"] is False
    assert captured_json["userCopy"] == ""
    assert captured_json["copyMode"] == "preserve"


def test_2_ad_copy_auto_generation_and_manual_copy_stay_separate_in_payload(
    monkeypatch,
) -> None:
    captured_json = _capture_generate_payload(monkeypatch)
    uploaded_file = SimpleNamespace(type="image/png", getvalue=lambda: b"source-image")
    format_label, detail_label = _labels_for_instagram_square()
    auto_copy = build_auto_copy(format_label, detail_label)

    api_client.request_backend(
        uploaded_file,
        "따뜻한 카페 배경으로 만들어줘",
        format_label,
        detail_label,
        ad_copy_prompt=auto_copy,
        copy_mode="polish",
    )

    assert "이미지 요청:" in str(captured_json["userPrompt"])
    assert "따뜻한 카페 배경으로 만들어줘" in str(captured_json["userPrompt"])
    assert captured_json["userCopy"] == auto_copy
    assert captured_json["copyMode"] == "polish"
    assert "CTA:" in auto_copy


def test_3_logo_upload_is_optional_and_serialized_as_data_url(monkeypatch) -> None:
    captured_json = _capture_generate_payload(monkeypatch)
    uploaded_file = SimpleNamespace(type="image/png", getvalue=lambda: b"source-image")
    logo_file = SimpleNamespace(type="image/png", getvalue=lambda: b"logo-image")
    format_label, detail_label = _labels_for_instagram_square()

    api_client.request_backend(
        uploaded_file,
        "로고가 어울리게 배치해줘",
        format_label,
        detail_label,
        logo_file=logo_file,
    )

    assert captured_json["logoDataUrl"] == (
        f"data:image/png;base64,{base64.b64encode(b'logo-image').decode('ascii')}"
    )
    assert captured_json["logoPosition"] == "bottom_right"

    captured_json_without_logo = _capture_generate_payload(monkeypatch)
    api_client.request_backend(
        uploaded_file,
        "로고 없이 만들어줘",
        format_label,
        detail_label,
    )

    assert captured_json_without_logo["logoDataUrl"] is None


def test_1_to_3_result_context_tracks_copy_mode_text_overlay_and_logo_hash() -> None:
    uploaded_file = SimpleNamespace(getvalue=lambda: b"source-image")
    logo_file = SimpleNamespace(getvalue=lambda: b"logo-image")
    format_label, detail_label = _labels_for_instagram_square()

    context = build_result_context(
        uploaded_file,
        "  제품 중앙 배치  ",
        format_label,
        detail_label,
        ad_copy_prompt="  헤드라인: 오늘의 메뉴  ",
        copy_mode="polish",
        text_overlay_enabled=True,
        logo_file=logo_file,
    )

    assert context is not None
    assert context["prompt"] == "제품 중앙 배치"
    assert context["adCopyPrompt"] == "헤드라인: 오늘의 메뉴"
    assert context["copyMode"] == "polish"
    assert context["textOverlayEnabled"] is True
    assert context["logoUploadHash"] == hashlib.sha256(b"logo-image").hexdigest()
