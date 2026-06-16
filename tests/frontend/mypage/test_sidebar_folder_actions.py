import httpx

from frontend.mypage import folder_management, sidebar
from frontend.mypage.state import FOLDER_NONE_VIEW, folder_view
from tests.frontend.mypage.sidebar_fakes import FakeStreamlit, patch_sidebar


def test_folder_error_detail_explains_missing_backend_folder_routes() -> None:
    request = httpx.Request("DELETE", "http://testserver/api/auth/me/folders/7")
    response = httpx.Response(404, json={"detail": "Not Found"}, request=request)
    exc = httpx.HTTPStatusError("Not Found", request=request, response=response)

    assert folder_management._folder_error_detail(exc, "fallback") == (
        "백엔드 서버가 폴더 이름변경/삭제 API를 아직 반영하지 않았습니다. "
        "백엔드를 재시작한 뒤 다시 시도해주세요."
    )


def test_sidebar_shows_management_menu_only_for_selected_user_folder(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    patch_sidebar(monkeypatch, fake_st)

    sidebar.render_sidebar(
        {"display_name": "User", "email": "user@example.com"},
        [{"id": 7, "name": "봄 신메뉴"}, {"id": 8, "name": "여름 신메뉴"}],
        folder_view(7),
        "jwt",
    )

    assert [popover["key"] for popover in fake_st.popovers] == ["mypage-folder-menu-7"]
    assert fake_st.popovers[0]["label"] == "⋯"
    assert any(button["key"] == "mypage-folder-none" for button in fake_st.buttons)
    assert any(button["key"] == "mypage-folder-7" for button in fake_st.buttons)
    assert any(button["key"] == "mypage-folder-8" for button in fake_st.buttons)
    assert any(
        button["key"] == "mypage-delete-folder-7" and button["label"] == "폴더 삭제"
        for button in fake_st.buttons
    )
    assert not any(popover["key"] == "mypage-folder-menu-8" for popover in fake_st.popovers)


def test_sidebar_renames_selected_folder_from_management_menu(monkeypatch) -> None:
    fake_st = FakeStreamlit(
        submitted_forms={"mypage-rename-folder-form-7"},
        text_values={"mypage-rename-folder-name-7": "여름 신메뉴"},
    )
    patch_sidebar(monkeypatch, fake_st)
    renamed: list[tuple[str, int, str]] = []
    monkeypatch.setattr(
        folder_management,
        "rename_my_folder",
        lambda access_token, folder_id, name: renamed.append((access_token, folder_id, name)),
    )

    sidebar.render_sidebar(
        {"display_name": "User", "email": "user@example.com"},
        [{"id": 7, "name": "봄 신메뉴"}],
        folder_view(7),
        "jwt",
    )

    assert renamed == [("jwt", 7, "여름 신메뉴")]
    assert fake_st.rerun_called is True


def test_sidebar_delete_menu_opens_confirmation_for_selected_folder(monkeypatch) -> None:
    fake_st = FakeStreamlit(clicked_keys={"mypage-delete-folder-7"})
    patch_sidebar(monkeypatch, fake_st)

    sidebar.render_sidebar(
        {"display_name": "User", "email": "user@example.com"},
        [{"id": 7, "name": "봄 신메뉴"}],
        folder_view(7),
        "jwt",
    )

    assert fake_st.session_state["mypage_delete_folder_confirm_id"] == 7
    assert fake_st.rerun_called is True


def test_sidebar_delete_confirmation_opens_as_dialog(monkeypatch) -> None:
    fake_st = FakeStreamlit(session_state={"mypage_delete_folder_confirm_id": 7})
    patch_sidebar(monkeypatch, fake_st)

    sidebar.render_sidebar(
        {"display_name": "User", "email": "user@example.com"},
        [{"id": 7, "name": "봄 신메뉴"}],
        folder_view(7),
        "jwt",
    )

    assert fake_st.dialogs == [{"title": "폴더 삭제"}]
    assert "폴더만 삭제되며, 폴더 안 이미지는 미분류로 이동됩니다." in fake_st.warnings


def test_sidebar_confirm_delete_deletes_folder_and_moves_view_to_uncategorized(
    monkeypatch,
) -> None:
    fake_st = FakeStreamlit(
        clicked_keys={"mypage-confirm-delete-folder-7"},
        session_state={"mypage_delete_folder_confirm_id": 7},
    )
    patch_sidebar(monkeypatch, fake_st)
    deleted: list[tuple[str, int]] = []
    monkeypatch.setattr(
        folder_management,
        "delete_my_folder",
        lambda access_token, folder_id: deleted.append((access_token, folder_id)),
    )

    sidebar.render_sidebar(
        {"display_name": "User", "email": "user@example.com"},
        [{"id": 7, "name": "봄 신메뉴"}],
        folder_view(7),
        "jwt",
    )

    assert "폴더만 삭제되며, 폴더 안 이미지는 미분류로 이동됩니다." in fake_st.warnings
    assert any(
        button["key"] == "mypage-confirm-delete-folder-7" and button["label"] == "폴더 삭제"
        for button in fake_st.buttons
    )
    assert deleted == [("jwt", 7)]
    assert fake_st.session_state["mypage_view"] == FOLDER_NONE_VIEW
    assert "mypage_delete_folder_confirm_id" not in fake_st.session_state
    assert fake_st.rerun_called is True
