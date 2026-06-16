import asyncio
import base64
import mimetypes
from pathlib import Path

from backend.app.db.models import Generation
from backend.app.services.storage_url import upload_url_if_exists_async


async def _file_to_image_data_url(path: Path) -> str | None:
    if not await asyncio.to_thread(path.is_file):
        return None

    content = await asyncio.to_thread(path.read_bytes)
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


async def _upload_item(row: Generation, used_count: int) -> dict[str, object] | None:
    if row.original_path is None:
        return None

    original_image_url = await upload_url_if_exists_async(row.original_path)
    if original_image_url is None:
        return None

    image_data_url = await _file_to_image_data_url(Path(row.original_path))

    return {
        "upload_id": row.image_hash,
        "original_image_url": original_image_url,
        "image_data_url": image_data_url,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "used_count": used_count,
    }
