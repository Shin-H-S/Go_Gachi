import logging
import mimetypes
from typing import Any

from backend.app.db.models import Generation
from backend.app.services.storage_url import output_download_url

logger = logging.getLogger(__name__)


async def _download_url_for_row(
    storage: Any,
    settings: Any,
    row: Generation,
    *,
    image_url: str | None,
) -> str | None:
    if row.output_path is None or row.status != "success" or image_url is None:
        return None

    filename = row.output_path.replace("\\", "/").rsplit("/", 1)[-1]
    if not filename:
        return None

    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    try:
        signed = await storage.download_url(
            row.output_path,
            filename=filename,
            content_type=content_type,
            expires_in=settings.download_url_ttl_seconds,
        )
    except Exception:
        logger.exception("download url create failed request_id=%s", row.request_id)
        signed = None
    return signed or output_download_url(row.output_path)
