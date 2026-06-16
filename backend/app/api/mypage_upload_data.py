import asyncio
import base64
import mimetypes
from pathlib import Path


async def _file_to_image_data_url(path: Path) -> str | None:
    if not await asyncio.to_thread(path.is_file):
        return None

    content = await asyncio.to_thread(path.read_bytes)
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"
