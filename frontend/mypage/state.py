from datetime import datetime

import streamlit as st

RECENT_VIEW = "recent"
UPLOADS_VIEW = "uploads"
ACCOUNT_VIEW = "account"
FOLDER_ALL_VIEW = "folder:all"
FOLDER_NONE_VIEW = "folder:none"
FOLDER_PREFIX = "folder:"


def format_date(value: str | None) -> str:
    if not value:
        return "-"
    try:
        return datetime.fromisoformat(value).strftime("%Y.%m.%d")
    except ValueError:
        return value[:10]


def profile_name(profile: dict) -> str:
    display_name = str(profile.get("display_name") or "").strip()
    email = str(profile.get("email") or "").strip()
    if display_name:
        return display_name
    if email and "@" in email:
        return email.split("@", 1)[0]
    return "닉네임"


def set_view(view: str) -> None:
    st.session_state["mypage_view"] = view


def folder_view(folder_id: int) -> str:
    return f"{FOLDER_PREFIX}{folder_id}"


def selected_folder_id(view: str) -> int | None:
    if not view.startswith(FOLDER_PREFIX) or view in {FOLDER_ALL_VIEW, FOLDER_NONE_VIEW}:
        return None
    try:
        return int(view.removeprefix(FOLDER_PREFIX))
    except ValueError:
        return None


def folder_name_by_id(folders: list[dict], folder_id: int | None) -> str:
    if folder_id is None:
        return "미분류"
    for folder in folders:
        if folder.get("id") == folder_id:
            return str(folder.get("name") or "폴더")
    return "폴더"


def view_title(view: str, folders: list[dict]) -> str:
    if view == RECENT_VIEW:
        return "전체 작업"
    if view == UPLOADS_VIEW:
        return "업로드한 메뉴 사진"
    if view == ACCOUNT_VIEW:
        return "계정 설정"
    if view == FOLDER_ALL_VIEW:
        return "전체"
    if view == FOLDER_NONE_VIEW:
        return "미분류"
    return folder_name_by_id(folders, selected_folder_id(view))


def folder_choices(folders: list[dict]) -> tuple[list[str], dict[str, int | None]]:
    labels = ["미분류"] + [str(folder["name"]) for folder in folders]
    mapping: dict[str, int | None] = {"미분류": None}
    for folder in folders:
        mapping[str(folder["name"])] = int(folder["id"])
    return labels, mapping


def filter_generations(items: list[dict], view: str) -> list[dict]:
    if view in {RECENT_VIEW, FOLDER_ALL_VIEW}:
        return items
    if view == FOLDER_NONE_VIEW:
        return [item for item in items if item.get("folder_id") is None]
    folder_id = selected_folder_id(view)
    return [item for item in items if item.get("folder_id") == folder_id]
