from frontend.mypage import views


def render_recent_work(
    generations: list[dict],
    folders: list[dict],
    access_token: str,
    *,
    total_count: int | None = None,
    current_page: int | None = None,
) -> None:
    views.render_recent_work(
        generations,
        folders,
        access_token,
        total_count=total_count,
        current_page=current_page,
    )


def render_folder_view(
    view: str,
    generations: list[dict],
    folders: list[dict],
    access_token: str,
    *,
    total_count: int | None = None,
    current_page: int | None = None,
) -> None:
    views.render_folder_view(
        view,
        generations,
        folders,
        access_token,
        total_count=total_count,
        current_page=current_page,
    )


def render_uploads(
    uploads: list[dict],
    *,
    total_count: int | None = None,
    current_page: int | None = None,
) -> None:
    views.render_uploads(
        uploads,
        total_count=total_count,
        current_page=current_page,
    )


def render_account_settings(profile: dict) -> None:
    views.render_account_settings(profile)
