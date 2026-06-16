from frontend.mypage import work_handoff
from frontend.work.uploads import get_handoff_uploaded_file


def test_prepare_generation_for_work_stores_selected_image_as_handoff_upload(
    monkeypatch,
) -> None:
    session_state = {
        "result_image_url": "old-url",
        "result_bytes": b"old",
        "result_copy": {"headline": "old"},
        "result_context": {"prompt": "old"},
    }
    monkeypatch.setattr(work_handoff, "request_asset_bytes", lambda url: b"selected")

    prepared = work_handoff.prepare_generation_for_work(
        session_state,
        {
            "request_id": "request-1",
            "image_url": "/outputs/result.png",
            "preset_id": "instagram",
        },
    )

    uploaded_file = get_handoff_uploaded_file(session_state)

    assert prepared is True
    assert uploaded_file is not None
    assert uploaded_file.name == "result.png"
    assert uploaded_file.type == "image/png"
    assert uploaded_file.getvalue() == b"selected"
    assert session_state["selected_channel"] == "인스타그램"
    assert "result_image_url" not in session_state
    assert "result_bytes" not in session_state
    assert "result_copy" not in session_state
    assert "result_context" not in session_state


def test_prepare_generation_for_work_returns_false_without_image_url() -> None:
    session_state: dict[str, object] = {}

    assert work_handoff.prepare_generation_for_work(session_state, {}) is False
    assert get_handoff_uploaded_file(session_state) is None
