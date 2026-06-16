"""로컬 디스크 저장소 구현."""

import asyncio
from pathlib import Path

from backend.app.core.config import Settings


class LocalStorage:
    """backend/uploads, backend/outputs 폴더를 사용하는 저장소."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def output_path(self, generation_id: str) -> str:
        return str(self.settings.output_dir / f"{generation_id}.png")

    def original_path(self, *, image_hash: str, extension: str, generation_id: str) -> str:
        _ = image_hash
        return str(self.settings.upload_dir / f"{generation_id}.{extension}")

    async def ensure_dirs(self) -> None:
        await asyncio.to_thread(self.settings.upload_dir.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(self.settings.output_dir.mkdir, parents=True, exist_ok=True)

    async def write_bytes(self, path: str, body: bytes, *, content_type: str) -> None:
        _ = content_type
        await self.ensure_dirs()
        await asyncio.to_thread(Path(path).write_bytes, body)

    async def read_bytes(self, path: str) -> bytes | None:
        file_path = Path(path)
        if not await asyncio.to_thread(file_path.is_file):
            return None
        return await asyncio.to_thread(file_path.read_bytes)

    async def download_url(
        self,
        path: str,
        *,
        filename: str,
        content_type: str,
        expires_in: int,
    ) -> str | None:
        _ = path, filename, content_type, expires_in
        return None

    async def exists(self, path: str) -> bool:
        return await asyncio.to_thread(Path(path).is_file)

    def output_url(self, path: str | None) -> str | None:
        filename = _filename(path)
        return f"/outputs/{filename}" if filename else None

    def upload_url(self, path: str | None) -> str | None:
        filename = _filename(path)
        return f"/uploads/{filename}" if filename else None

    async def output_url_if_exists(self, path: str | None) -> str | None:
        if path is None or not await self.exists(path):
            return None
        return self.output_url(path)

    async def upload_url_if_exists(self, path: str | None) -> str | None:
        if path is None or not await self.exists(path):
            return None
        return self.upload_url(path)


def _filename(path: str | None) -> str | None:
    if path is None:
        return None
    filename = Path(path).name
    return filename or None
