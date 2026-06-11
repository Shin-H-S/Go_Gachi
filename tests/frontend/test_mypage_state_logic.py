from frontend.mypage import state


def test_profile_name_prefers_display_name_then_email_prefix() -> None:
    assert state.profile_name({"display_name": "  Store Owner  ", "email": "a@b.com"}) == (
        "Store Owner"
    )
    assert state.profile_name({"display_name": "", "email": "owner@example.com"}) == "owner"


def test_folder_view_helpers_build_titles_and_choices() -> None:
    folders = [{"id": 7, "name": "Spring"}, {"id": 8, "name": "Summer"}]
    labels, mapping = state.folder_choices(folders)

    assert state.folder_view(7) == "folder:7"
    assert state.selected_folder_id("folder:7") == 7
    assert state.selected_folder_id("folder:not-a-number") is None
    assert state.view_title("folder:8", folders) == "Summer"
    assert mapping[labels[0]] is None
    assert mapping["Spring"] == 7
    assert mapping["Summer"] == 8


def test_recent_view_title_is_labeled_as_all_work() -> None:
    assert state.view_title(state.RECENT_VIEW, []) == "전체 작업"


def test_filter_generations_matches_recent_all_uncategorized_and_folder_views() -> None:
    uncategorized = {"request_id": "none", "folder_id": None}
    spring = {"request_id": "spring", "folder_id": 7}
    summer = {"request_id": "summer", "folder_id": 8}
    items = [uncategorized, spring, summer]

    assert state.filter_generations(items, state.RECENT_VIEW) == items
    assert state.filter_generations(items, state.FOLDER_ALL_VIEW) == items
    assert state.filter_generations(items, state.FOLDER_NONE_VIEW) == [uncategorized]
    assert state.filter_generations(items, "folder:7") == [spring]


def test_format_date_handles_empty_iso_and_fallback_values() -> None:
    assert state.format_date(None) == "-"
    assert state.format_date("2026-06-08T12:34:56") == "2026.06.08"
    assert state.format_date("2026/06/08 12:34") == "2026/06/08"
