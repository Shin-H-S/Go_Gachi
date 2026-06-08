import hashlib
import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT_DIR = Path(__file__).resolve().parents[1]


def import_frontend_module(module_name: str):
    root_path = str(ROOT_DIR)
    if root_path not in sys.path:
        sys.path.insert(0, root_path)

    return importlib.import_module(module_name)


def first_format_and_detail(format_options):
    format_label = next(iter(format_options))
    detail = format_options[format_label]["details"][0]
    return format_label, detail


def test_router_normalizes_query_param_page_names() -> None:
    router = import_frontend_module("frontend.core.router")

    assert router.normalize_page_name("main") == "main"
    assert router.normalize_page_name("work") == "work"
    assert router.normalize_page_name("mypage") == "mypage"
    assert router.normalize_page_name("missing") == "main"
    assert router.normalize_page_name(["work", "main"]) == "work"
    assert router.normalize_page_name([]) == "main"
    assert router.normalize_page_name(None) == "main"


def test_router_navigation_writes_normalized_page_to_query_params(monkeypatch) -> None:
    router = import_frontend_module("frontend.core.router")
    fake_st = SimpleNamespace(query_params={})
    monkeypatch.setattr(router, "st", fake_st)

    router.navigate_to("work")

    assert fake_st.query_params["page"] == "work"

    router.navigate_to("login")

    assert fake_st.query_params["page"] == "login"

    router.navigate_to("signup")

    assert fake_st.query_params["page"] == "signup"

    router.navigate_to("mypage")

    assert fake_st.query_params["page"] == "mypage"


def test_init_session_state_sets_default_selected_channel(monkeypatch) -> None:
    router = import_frontend_module("frontend.core.router")
    fake_st = SimpleNamespace(session_state={})
    monkeypatch.setattr(router, "st", fake_st)

    router.init_session_state()

    assert fake_st.session_state["selected_channel"] == next(iter(router.FORMAT_OPTIONS))


def test_selected_channel_falls_back_to_first_configured_preset(monkeypatch) -> None:
    work_state = import_frontend_module("frontend.work.state")
    fake_format_options = {
        "테스트 채널": {"value": "test_channel", "details": []},
        "두번째 채널": {"value": "second_channel", "details": []},
    }
    fake_st = SimpleNamespace(session_state={"selected_channel": "없는 채널"})
    monkeypatch.setattr(work_state, "FORMAT_OPTIONS", fake_format_options)
    monkeypatch.setattr(work_state, "st", fake_st)

    selected_channel = work_state.get_selected_channel()

    assert selected_channel == "테스트 채널"
    assert fake_st.session_state["selected_channel"] == "테스트 채널"


def test_result_context_uses_trimmed_prompt_upload_hash_and_selected_preset() -> None:
    work_state = import_frontend_module("frontend.work.state")
    format_label, detail = first_format_and_detail(work_state.FORMAT_OPTIONS)
    image_bytes = b"uploaded image"
    uploaded_file = SimpleNamespace(getvalue=lambda: image_bytes)

    context = work_state.build_result_context(
        uploaded_file,
        "  make this menu look bright  ",
        format_label,
        str(detail["label"]),
    )

    assert context == {
        "presetId": work_state.FORMAT_OPTIONS[format_label]["value"],
        "detailType": detail["id"],
        "targetWidth": detail["size"][0],
        "targetHeight": detail["size"][1],
        "prompt": "make this menu look bright",
        "uploadHash": hashlib.sha256(image_bytes).hexdigest(),
    }


def test_result_context_requires_upload_and_prompt() -> None:
    work_state = import_frontend_module("frontend.work.state")
    format_label, detail = first_format_and_detail(work_state.FORMAT_OPTIONS)
    uploaded_file = SimpleNamespace(getvalue=lambda: b"uploaded image")

    assert work_state.build_result_context(None, "prompt", format_label, detail["label"]) is None
    assert (
        work_state.build_result_context(uploaded_file, "   ", format_label, detail["label"])
        is None
    )


def test_sync_result_state_clears_stale_generated_result(monkeypatch) -> None:
    work_state = import_frontend_module("frontend.work.state")
    fake_st = SimpleNamespace(
        session_state={
            "result_bytes": b"old-result",
            "result_context": {"prompt": "old"},
        }
    )
    monkeypatch.setattr(work_state, "st", fake_st)

    work_state.sync_result_state({"prompt": "new"})

    assert "result_bytes" not in fake_st.session_state
    assert "result_context" not in fake_st.session_state


def test_sync_result_state_keeps_matching_generated_result(monkeypatch) -> None:
    work_state = import_frontend_module("frontend.work.state")
    result_context = {"prompt": "same"}
    fake_st = SimpleNamespace(
        session_state={
            "result_bytes": b"current-result",
            "result_context": result_context,
        }
    )
    monkeypatch.setattr(work_state, "st", fake_st)

    work_state.sync_result_state(result_context)

    assert fake_st.session_state["result_bytes"] == b"current-result"
    assert fake_st.session_state["result_context"] == result_context
