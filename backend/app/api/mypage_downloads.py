import logging
import mimetypes
from collections.abc import Sequence
from typing import Any

from backend.app.db.models import Generation
from backend.app.services.storage.r2 import R2Storage
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


async def build_download_urls(
    storage: Any,
    settings: Any,
    rows: Sequence[Generation],
    image_urls: Sequence[str | None],
) -> list[str | None]:
    download_urls: list[str | None] = [None] * len(rows)
    if not rows:
        return download_urls

    if not isinstance(storage, R2Storage):
        for index, (row, image_url) in enumerate(zip(rows, image_urls, strict=True)):
            download_urls[index] = await _download_url_for_row(
                storage,
                settings,
                row,
                image_url=image_url,
            )
        return download_urls

    batch_items: list[dict[str, str]] = []
    batch_positions: list[int] = []
    for index, (row, image_url) in enumerate(zip(rows, image_urls, strict=True)):
        if row.output_path is None or row.status != "success" or image_url is None:
            continue
        filename = row.output_path.replace("\\", "/").rsplit("/", 1)[-1]
        if not filename:
            continue
        batch_items.append(
            {
                "path": row.output_path,
                "filename": filename,
                "content_type": (mimetypes.guess_type(filename)[0] or "application/octet-stream"),
            }
        )
        batch_positions.append(index)

    if not batch_items:
        return download_urls

    try:
        signed_urls = await storage.download_urls(
            batch_items,
            expires_in=settings.download_url_ttl_seconds,
        )
    except Exception:
        logger.exception("download url batch create failed")
        signed_urls = [None] * len(batch_items)

    for index, signed in zip(batch_positions, signed_urls, strict=True):
        row = rows[index]
        download_urls[index] = signed or output_download_url(row.output_path)
    return download_urls
