from types import SimpleNamespace

from frontend import api_client
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


def test_1_ad_copy_disabled_skips_user_copy_and_forces_preserve_mode(
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
        ad_copy_enabled=False,
        copy_mode="preserve",
        ad_copy_prompt="이미지에 들어가면 안 되는 문구",
    )

    assert result.image_bytes == b"result"
    assert captured_json["adCopyEnabled"] is False
    assert captured_json["userCopy"] == ""
    assert captured_json["copyMode"] == "preserve"


def test_2_ad_copy_text_and_image_prompt_stay_separate_in_payload(
    monkeypatch,
) -> None:
    captured_json = _capture_generate_payload(monkeypatch)
    uploaded_file = SimpleNamespace(type="image/png", getvalue=lambda: b"source-image")
    format_label, detail_label = _labels_for_instagram_square()
    ad_copy = "헤드라인: 백엔드가 만든 문구\n서브카피: 메뉴 분위기를 살려줘요.\nCTA: 자세히 보기"

    api_client.request_backend(
        uploaded_file,
        "따뜻한 카페 배경으로 만들어줘",
        format_label,
        detail_label,
        ad_copy_prompt=ad_copy,
        copy_mode="polish",
    )

    assert "이미지 요청:" in str(captured_json["userPrompt"])
    assert "따뜻한 카페 배경으로 만들어줘" in str(captured_json["userPrompt"])
    assert captured_json["userCopy"] == ad_copy
    assert captured_json["copyMode"] == "polish"


def test_4_rewrite_mode_sends_user_copy_and_keeps_rewritten_copy_response(
    monkeypatch,
) -> None:
    rewritten_copy = {
        "headline": "오늘 놓치기 아까운 딸기 케이크 6,500원",
        "subcopy": "카페에서 즐기는 신선한 메뉴를 더 맛있게 전해드려요.",
        "cta": "지금 방문해보세요",
        "copyMode": "rewrite",
    }
    captured_json = _capture_generate_payload(
        monkeypatch,
        result_payload={
            "imageDataUrl": "data:image/png;base64,cmVzdWx0",
            "copy": rewritten_copy,
        },
    )
    uploaded_file = SimpleNamespace(type="image/png", getvalue=lambda: b"source-image")
    format_label, detail_label = _labels_for_instagram_square()

    result = api_client.request_backend(
        uploaded_file,
        "따뜻한 카페 배경으로 만들어줘",
        format_label,
        detail_label,
        ad_copy_prompt="딸기 케이크 6500원",
        copy_mode="rewrite",
        ad_copy_enabled=True,
    )

    assert captured_json["adCopyEnabled"] is True
    assert captured_json["userCopy"] == "딸기 케이크 6500원"
    assert captured_json["copyMode"] == "rewrite"
    assert result.copy == rewritten_copy


def test_3_generate_payload_omits_logo_fields(monkeypatch) -> None:
    captured_json = _capture_generate_payload(monkeypatch)
    uploaded_file = SimpleNamespace(type="image/png", getvalue=lambda: b"source-image")
    format_label, detail_label = _labels_for_instagram_square()

    api_client.request_backend(
        uploaded_file,
        "깔끔하게 만들어줘",
        format_label,
        detail_label,
    )

    assert "logoDataUrl" not in captured_json
    assert "logoPosition" not in captured_json


def test_1_to_3_result_context_tracks_copy_mode_and_ad_copy() -> None:
    uploaded_file = SimpleNamespace(getvalue=lambda: b"source-image")
    format_label, detail_label = _labels_for_instagram_square()

    context = build_result_context(
        uploaded_file,
        "  제품 중앙 배치  ",
        format_label,
        detail_label,
        ad_copy_prompt="  헤드라인: 오늘의 메뉴  ",
        copy_mode="polish",
        ad_copy_enabled=True,
    )

    assert context is not None
    assert context["prompt"] == "제품 중앙 배치"
    assert context["adCopyPrompt"] == "헤드라인: 오늘의 메뉴"
    assert context["copyMode"] == "polish"
    assert context["adCopyEnabled"] is True
    assert "logoUploadHash" not in context
    assert "logoPosition" not in context
