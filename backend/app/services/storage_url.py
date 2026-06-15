"""저장된 파일 경로/key를 프론트가 쓸 수 있는 URL로 변환한다."""

from pathlib import Path, PurePosixPath

from backend.app.core.config import get_settings
from backend.app.services.storage import get_storage


def _asset_download_url(prefix: str, path: str | None) -> str | None:
    if path is None:
        return None
    filename = PurePosixPath(str(path).replace("\\", "/")).name
    return f"/api/assets/download/{prefix}/{filename}" if filename else None


def output_url(output_path: str | None) -> str | None:
    """저장된 결과 이미지의 외부 접근 URL을 만든다."""
    settings = get_settings()
    return get_storage(settings).output_url(output_path)


def output_download_url(output_path: str | None) -> str | None:
    """생성 결과 이미지를 다운로드하는 백엔드 URL을 만든다."""
    return _asset_download_url("outputs", output_path)


def upload_url(upload_path: str | None) -> str | None:
    """업로드 원본 이미지의 외부 접근 URL을 만든다."""
    settings = get_settings()
    return get_storage(settings).upload_url(upload_path)


def upload_download_url(upload_path: str | None) -> str | None:
    """업로드 원본 이미지를 다운로드하는 백엔드 URL을 만든다."""
    return _asset_download_url("uploads", upload_path)


def output_url_if_exists(output_path: str | None) -> str | None:
    """결과 이미지가 존재할 때만 URL을 만든다."""
    settings = get_settings()
    storage = get_storage(settings)
    if settings.storage_backend == "r2":
        return storage.output_url(output_path)
    return output_url(output_path) if _local_file_exists(output_path) else None


def upload_url_if_exists(upload_path: str | None) -> str | None:
    """업로드 원본 이미지가 존재할 때만 URL을 만든다."""
    settings = get_settings()
    storage = get_storage(settings)
    if settings.storage_backend == "r2":
        return storage.upload_url(upload_path)
    return upload_url(upload_path) if _local_file_exists(upload_path) else None


async def output_url_if_exists_async(output_path: str | None) -> str | None:
    """``output_url_if_exists``의 비동기 버전."""
    settings = get_settings()
    return await get_storage(settings).output_url_if_exists(output_path)


async def upload_url_if_exists_async(upload_path: str | None) -> str | None:
    """``upload_url_if_exists``의 비동기 버전."""
    settings = get_settings()
    return await get_storage(settings).upload_url_if_exists(upload_path)


def _local_file_exists(path: str | None) -> bool:
    if path is None:
        return False
    return Path(path).is_file()
