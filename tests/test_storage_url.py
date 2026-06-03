from pathlib import Path

from backend.app.services.storage_url import public_output_url, public_output_url_if_exists


def test_public_output_url_returns_root_relative_path() -> None:
    assert public_output_url(Path("C:/tmp/backend/outputs/result.png")) == "/outputs/result.png"


def test_public_output_url_returns_none_for_missing_path() -> None:
    assert public_output_url(None) is None


def test_public_output_url_if_exists_returns_none_for_missing_file(tmp_path) -> None:
    assert public_output_url_if_exists(tmp_path / "missing.png") is None
