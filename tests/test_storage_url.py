import asyncio
from pathlib import Path

import pytest

from backend.app.core.config import get_settings
from backend.app.services.storage_url import (
    output_url,
    output_url_if_exists,
    output_url_if_exists_async,
    upload_url,
    upload_url_if_exists,
    upload_url_if_exists_async,
)


@pytest.fixture
def local_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    """캐시된 settings의 storage_backend를 local로 강제한다."""
    settings = get_settings()
    monkeypatch.setattr(settings, "storage_backend", "local")


@pytest.fixture
def r2_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    """캐시된 settings의 storage_backend를 r2로, public URL을 고정값으로 강제한다."""
    settings = get_settings()
    monkeypatch.setattr(settings, "storage_backend", "r2")
    monkeypatch.setattr(settings, "r2_public_url", "https://pub-test.r2.dev")


def test_output_url_returns_root_relative_path(local_storage: None) -> None:
    assert output_url(Path("C:/tmp/backend/outputs/result.png")) == "/outputs/result.png"


def test_upload_url_returns_root_relative_path(local_storage: None) -> None:
    assert upload_url(Path("C:/tmp/backend/uploads/original.png")) == "/uploads/original.png"


def test_output_url_returns_none_for_missing_path(local_storage: None) -> None:
    assert output_url(None) is None


def test_upload_url_returns_none_for_missing_path(local_storage: None) -> None:
    assert upload_url(None) is None


def test_output_url_if_exists_returns_none_for_missing_file(
    local_storage: None, tmp_path: Path
) -> None:
    assert output_url_if_exists(tmp_path / "missing.png") is None


def test_upload_url_if_exists_returns_none_for_missing_file(
    local_storage: None, tmp_path: Path
) -> None:
    assert upload_url_if_exists(tmp_path / "missing.png") is None


def test_output_url_if_exists_async_returns_path_for_existing_file(
    local_storage: None, tmp_path: Path
) -> None:
    output_file = tmp_path / "result.png"
    output_file.write_bytes(b"fake png")

    assert asyncio.run(output_url_if_exists_async(output_file)) == "/outputs/result.png"


def test_upload_url_if_exists_async_returns_path_for_existing_file(
    local_storage: None, tmp_path: Path
) -> None:
    upload_file = tmp_path / "original.png"
    upload_file.write_bytes(b"fake png")

    assert asyncio.run(upload_url_if_exists_async(upload_file)) == "/uploads/original.png"


def test_output_url_if_exists_async_returns_none_for_missing_file(
    local_storage: None, tmp_path: Path
) -> None:
    assert asyncio.run(output_url_if_exists_async(tmp_path / "missing.png")) is None


def test_upload_url_if_exists_async_returns_none_for_missing_file(
    local_storage: None, tmp_path: Path
) -> None:
    assert asyncio.run(upload_url_if_exists_async(tmp_path / "missing.png")) is None


def test_output_url_if_exists_async_returns_none_for_none_path(local_storage: None) -> None:
    assert asyncio.run(output_url_if_exists_async(None)) is None


def test_upload_url_if_exists_async_returns_none_for_none_path(local_storage: None) -> None:
    assert asyncio.run(upload_url_if_exists_async(None)) is None


# r2 모드 검증


def test_output_url_returns_r2_public_url_in_r2_mode(r2_storage: None) -> None:
    assert (
        output_url(Path("/tmp/backend/outputs/result.png"))
        == "https://pub-test.r2.dev/outputs/result.png"
    )


def test_upload_url_returns_r2_public_url_in_r2_mode(r2_storage: None) -> None:
    assert (
        upload_url(Path("/tmp/backend/uploads/original.png"))
        == "https://pub-test.r2.dev/uploads/original.png"
    )


def test_output_url_if_exists_async_skips_disk_check_in_r2_mode(
    r2_storage: None, tmp_path: Path
) -> None:
    # r2 모드에서는 디스크 파일이 없어도 URL을 만든다(R2 객체 존재는 DB 기록 신뢰).
    missing = tmp_path / "missing.png"
    assert (
        asyncio.run(output_url_if_exists_async(missing))
        == "https://pub-test.r2.dev/outputs/missing.png"
    )
