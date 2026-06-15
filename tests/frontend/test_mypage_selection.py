from frontend.mypage import selection


def test_toggle_selected_generation_ids_selects_and_deselects() -> None:
    session_state: dict[str, object] = {}

    selection.toggle_generation_selection(session_state, "request-1")
    assert selection.selected_generation_ids(session_state) == ["request-1"]

    selection.toggle_generation_selection(session_state, "request-2")
    assert selection.selected_generation_ids(session_state) == ["request-1", "request-2"]

    selection.toggle_generation_selection(session_state, "request-1")
    assert selection.selected_generation_ids(session_state) == ["request-2"]


def test_generation_action_availability_depends_on_selection_count() -> None:
    assert selection.action_availability(0) == {
        "single": False,
        "download": False,
        "multi": False,
    }
    assert selection.action_availability(1) == {
        "single": True,
        "download": True,
        "multi": False,
    }
    assert selection.action_availability(2) == {
        "single": False,
        "download": True,
        "multi": True,
    }


def test_selected_generation_items_preserves_current_list_order() -> None:
    items = [
        {"request_id": "request-1"},
        {"request_id": "request-2"},
        {"request_id": "request-3"},
    ]

    assert selection.selected_generation_items(items, ["request-3", "request-1"]) == [
        {"request_id": "request-1"},
        {"request_id": "request-3"},
    ]
