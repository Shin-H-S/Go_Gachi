import httpx

from frontend.core.config import BACKEND_URL


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"} if access_token else {}


def _get_json(path: str, access_token: str, timeout: int = 30) -> dict:
    response = httpx.get(
        f"{BACKEND_URL}{path}",
        headers=_auth_headers(access_token),
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def request_me(access_token: str) -> dict:
    return _get_json("/api/auth/me", access_token)


def request_my_generations(access_token: str, page: int = 1) -> dict:
    page = max(1, int(page))
    path = "/api/auth/me/generations" if page == 1 else f"/api/auth/me/generations?page={page}"
    return _get_json(path, access_token)


def request_my_folders(access_token: str) -> dict:
    return _get_json("/api/auth/me/folders", access_token)


def request_my_uploads(access_token: str) -> dict:
    return _get_json("/api/auth/me/uploads", access_token)


def create_my_folder(access_token: str, name: str) -> dict:
    response = httpx.post(
        f"{BACKEND_URL}/api/auth/me/folders",
        json={"name": name},
        headers=_auth_headers(access_token),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def rename_my_folder(access_token: str, folder_id: int, name: str) -> dict:
    response = httpx.patch(
        f"{BACKEND_URL}/api/auth/me/folders/{folder_id}",
        json={"name": name},
        headers=_auth_headers(access_token),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def delete_my_folder(access_token: str, folder_id: int) -> None:
    response = httpx.delete(
        f"{BACKEND_URL}/api/auth/me/folders/{folder_id}",
        headers=_auth_headers(access_token),
        timeout=30,
    )
    response.raise_for_status()


def move_generation_to_folder(
    access_token: str,
    request_id: str,
    folder_id: int | None,
) -> dict:
    response = httpx.patch(
        f"{BACKEND_URL}/api/auth/me/generations/{request_id}/folder",
        json={"folder_id": folder_id},
        headers=_auth_headers(access_token),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
