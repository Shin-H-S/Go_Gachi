"""Streamlit 프론트에서 백엔드 API를 호출하는 헬퍼."""

from __future__ import annotations

import os
from typing import Any

import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "")


def backend_url(path: str) -> str:
    # GCP 배포 URL을 명시하지 않으면 잘못된 서버로 요청하지 않게 즉시 실패시킨다.
    if not BACKEND_URL:
        raise RuntimeError("BACKEND_URL is not configured.")
    return f"{BACKEND_URL.rstrip('/')}/{path.lstrip('/')}"


async def get_config() -> dict[str, Any]:
    """프론트 초기 렌더링에 필요한 프리셋 목록을 가져온다."""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(backend_url("/api/config"))
        response.raise_for_status()
        return response.json()


async def generate(image_data_url: str, preset_id: str, feedback: str = "") -> dict[str, Any]:
    """사용자 이미지와 선택 프리셋을 백엔드 생성 API로 보낸다."""
    payload = {
        "imageDataUrl": image_data_url,
        "presetId": preset_id,
        "feedback": feedback,
    }
    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(backend_url("/api/generate"), json=payload)
        response.raise_for_status()
        return response.json()
