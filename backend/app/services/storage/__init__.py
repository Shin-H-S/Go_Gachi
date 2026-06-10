"""저장소 backend 선택 진입점."""

from backend.app.core.config import Settings
from backend.app.services.storage.base import Storage
from backend.app.services.storage.local import LocalStorage
from backend.app.services.storage.r2 import R2Storage


def get_storage(settings: Settings) -> Storage:
    """환경 설정에 맞는 저장소 구현을 돌려준다."""
    if settings.storage_backend == "r2":
        return R2Storage(settings)
    return LocalStorage(settings)


__all__ = ["Storage", "get_storage"]
