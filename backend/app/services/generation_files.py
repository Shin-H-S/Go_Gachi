"""이미지 생성 흐름에서 쓰는 파일·식별자 헬퍼."""

import asyncio
import base64
import uuid
from datetime import datetime
from pathlib import Path


def new_generation_id() -> str:
    """DB 행·로컬 파일명용 ``YYYYMMDD_HHMMSS_<6hex>`` 형식 ID를 발급한다(시간순 정렬·식별용)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{uuid.uuid4().hex[:6]}"


async def file_to_data_url(path: Path) -> str:
    """저장된 PNG 파일을 base64 data URL로 인코딩한다(캐시 hit 응답용)."""
    content = await asyncio.to_thread(path.read_bytes)
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:image/png;base64,{encoded}"
