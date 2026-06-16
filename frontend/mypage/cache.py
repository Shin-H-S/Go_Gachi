import streamlit as st

from frontend.services.api_client import (
    request_me,
    request_my_folders,
    request_my_generations,
    request_my_uploads,
)

PROFILE_CACHE_TTL_SECONDS = 60
FOLDERS_CACHE_TTL_SECONDS = 60
GENERATIONS_CACHE_TTL_SECONDS = 30
UPLOADS_CACHE_TTL_SECONDS = 60


@st.cache_data(show_spinner=False, ttl=PROFILE_CACHE_TTL_SECONDS)
def cached_request_me(access_token: str) -> dict:
    return request_me(access_token)


@st.cache_data(show_spinner=False, ttl=FOLDERS_CACHE_TTL_SECONDS)
def cached_request_my_folders(access_token: str) -> dict:
    return request_my_folders(access_token)


@st.cache_data(show_spinner=False, ttl=GENERATIONS_CACHE_TTL_SECONDS)
def cached_request_my_generations(
    access_token: str,
    page: int = 1,
    folder_id: int | None = None,
) -> dict:
    return request_my_generations(access_token, page=page, folder_id=folder_id)


@st.cache_data(show_spinner=False, ttl=UPLOADS_CACHE_TTL_SECONDS)
def cached_request_my_uploads(access_token: str) -> dict:
    return request_my_uploads(access_token)


def clear_generation_cache() -> None:
    cached_request_my_generations.clear()


def clear_mypage_cache() -> None:
    cached_request_me.clear()
    cached_request_my_folders.clear()
    cached_request_my_generations.clear()
    cached_request_my_uploads.clear()
