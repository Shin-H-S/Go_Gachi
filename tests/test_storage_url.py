import asyncio
from pathlib import Path

from backend.app.services.storage_url import (
    output_url,
    output_url_if_exists,
    output_url_if_exists_async,
)


def test_output_url_returns_root_relative_path() -> None:
    assert output_url(Path("C:/tmp/backend/outputs/result.png")) == "/outputs/result.png"


def test_output_url_returns_none_for_missing_path() -> None:
    assert output_url(None) is None


def test_output_url_if_exists_returns_none_for_missing_file(tmp_path) -> None:
    assert output_url_if_exists(tmp_path / "missing.png") is None


def test_output_url_if_exists_async_returns_path_for_existing_file(tmp_path) -> None:
    output_file = tmp_path / "result.png"
    output_file.write_bytes(b"fake png")

    assert asyncio.run(output_url_if_exists_async(output_file)) == "/outputs/result.png"


def test_output_url_if_exists_async_returns_none_for_missing_file(tmp_path) -> None:
    assert asyncio.run(output_url_if_exists_async(tmp_path / "missing.png")) is None


def test_output_url_if_exists_async_returns_none_for_none_path() -> None:
    assert asyncio.run(output_url_if_exists_async(None)) is None
