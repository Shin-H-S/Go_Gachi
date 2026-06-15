from types import SimpleNamespace

from frontend.work.uploads import (
    clear_handoff_uploaded_file,
    get_effective_uploaded_file,
    get_handoff_uploaded_file,
    set_handoff_uploaded_file,
)


def test_handoff_uploaded_file_behaves_like_streamlit_upload() -> None:
    session_state: dict[str, object] = {}

    set_handoff_uploaded_file(
        session_state,
        image_bytes=b"generated-image",
        file_name="result.webp",
        mime_type="image/webp",
    )

    uploaded_file = get_handoff_uploaded_file(session_state)

    assert uploaded_file is not None
    assert uploaded_file.name == "result.webp"
    assert uploaded_file.type == "image/webp"
    assert uploaded_file.getvalue() == b"generated-image"


def test_effective_uploaded_file_uses_handoff_when_no_real_upload() -> None:
    session_state = {
        "work_handoff_upload_bytes": b"generated-image",
        "work_handoff_upload_name": "result.png",
        "work_handoff_upload_type": "image/png",
    }

    uploaded_file = get_effective_uploaded_file([], session_state)

    assert uploaded_file is not None
    assert uploaded_file.getvalue() == b"generated-image"


def test_effective_uploaded_file_prefers_real_upload_and_clears_handoff() -> None:
    real_file = SimpleNamespace(name="menu.png", type="image/png", getvalue=lambda: b"menu")
    session_state = {
        "work_handoff_upload_bytes": b"generated-image",
        "work_handoff_upload_name": "result.png",
        "work_handoff_upload_type": "image/png",
    }

    uploaded_file = get_effective_uploaded_file([real_file], session_state)

    assert uploaded_file is real_file
    assert get_handoff_uploaded_file(session_state) is None


def test_clear_handoff_uploaded_file_removes_all_handoff_keys() -> None:
    session_state = {
        "work_handoff_upload_bytes": b"generated-image",
        "work_handoff_upload_name": "result.png",
        "work_handoff_upload_type": "image/png",
    }

    clear_handoff_uploaded_file(session_state)

    assert session_state == {}
