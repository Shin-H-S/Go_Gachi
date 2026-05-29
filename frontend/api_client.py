import base64
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

try:
    from frontend.config import FORMAT_OPTIONS
except ModuleNotFoundError:
    from config import FORMAT_OPTIONS

load_dotenv(Path(__file__).with_name(".env"))
BACKEND_URL = os.getenv("BACKEND_URL", "").rstrip("/")


def file_to_data_url(uploaded_file) -> str:
    mime_type = uploaded_file.type or "application/octet-stream"
    encoded = base64.b64encode(uploaded_file.getvalue()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def data_url_to_bytes(data_url: str) -> bytes:
    if "," not in data_url:
        raise ValueError("백엔드 응답 imageDataUrl 형식이 올바르지 않습니다.")

    header, encoded = data_url.split(",", 1)
    if ";base64" not in header:
        raise ValueError("백엔드 응답 imageDataUrl은 base64 데이터 URL이어야 합니다.")

    return base64.b64decode(encoded)


def build_feedback(prompt: str, detail_label: str) -> str:
    return f"광고 유형: {detail_label}\n{prompt.strip()}"


def request_backend(uploaded_file, prompt: str, format_label: str, detail_label: str) -> bytes:
    if not BACKEND_URL:
        raise RuntimeError("BACKEND_URL이 설정되어 있지 않습니다.")

    payload = {
        "imageDataUrl": file_to_data_url(uploaded_file),
        "presetId": FORMAT_OPTIONS[format_label]["value"],
        "feedback": build_feedback(prompt, detail_label),
    }

    response = httpx.post(f"{BACKEND_URL}/api/generate", json=payload, timeout=90)
    response.raise_for_status()
    data = response.json()
    image_data_url = data.get("imageDataUrl")
    if not image_data_url:
        raise ValueError("백엔드 응답에 imageDataUrl이 없습니다.")

    return data_url_to_bytes(image_data_url)
