from backend.app.db.models import Generation
from backend.app.services.storage_url import upload_url_if_exists_async


async def _upload_item(row: Generation, used_count: int) -> dict[str, object] | None:
    if row.original_path is None:
        return None

    original_image_url = await upload_url_if_exists_async(row.original_path)
    if original_image_url is None:
        return None

    return {
        "upload_id": row.image_hash,
        "original_image_url": original_image_url,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "used_count": used_count,
    }
