from backend.app.core.config import get_settings
from backend.app.services.storage.local import LocalStorage
from backend.app.services.storage.r2 import R2Storage


def test_r2_original_path_uses_generation_id(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "r2_public_url", "https://pub-test.r2.dev")

    storage = R2Storage(settings)

    assert (
        storage.original_path(
            image_hash="a" * 64,
            extension="png",
            generation_id="20260610_120000_abcdef",
        )
        == "uploads/20260610_120000_abcdef.png"
    )


def test_local_and_r2_original_path_use_same_filename_policy(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", settings.data_dir / "uploads")

    local_storage = LocalStorage(settings)
    r2_storage = R2Storage(settings)

    local_path = local_storage.original_path(
        image_hash="b" * 64,
        extension="jpg",
        generation_id="20260610_121000_abcdef",
    )
    r2_path = r2_storage.original_path(
        image_hash="b" * 64,
        extension="jpg",
        generation_id="20260610_121000_abcdef",
    )

    assert local_path.endswith("20260610_121000_abcdef.jpg")
    assert r2_path == "uploads/20260610_121000_abcdef.jpg"
