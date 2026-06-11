import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

FRONTEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = FRONTEND_DIR.parent
CONFIG_PRESETS_PATH = ROOT_DIR / "config" / "presets.json"
CHANNEL_ASSET_DIR = FRONTEND_DIR / "assets"
DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"

# 공통 설정은 레포 최상단 .env에서 읽고, 프론트 전용 .env가 있으면 그 값으로 덮어쓴다.
load_dotenv(ROOT_DIR / ".env")
load_dotenv(FRONTEND_DIR / ".env", override=True)

BACKEND_URL = os.getenv("BACKEND_URL", DEFAULT_BACKEND_URL).rstrip("/")
FRONTEND_CONFIG_SOURCE = os.getenv("FRONTEND_CONFIG_SOURCE", "auto").lower()


def _load_local_presets() -> list[dict[str, object]]:
    """백엔드가 없을 때 사용할 로컬 프리셋 파일을 읽는다."""
    return json.loads(CONFIG_PRESETS_PATH.read_text(encoding="utf-8"))


def _load_backend_presets() -> list[dict[str, object]]:
    """백엔드 /api/config에서 프론트 표시용 프리셋을 읽는다."""
    response = httpx.get(f"{BACKEND_URL}/api/config", timeout=2)
    response.raise_for_status()
    payload = response.json()
    presets = payload.get("presets") if isinstance(payload, dict) else None
    if not isinstance(presets, list):
        raise ValueError("백엔드 config 응답에 presets가 없습니다.")
    return presets


def load_presets() -> list[dict[str, object]]:
    """설정 소스 우선순위에 따라 프리셋 목록을 가져온다."""
    if FRONTEND_CONFIG_SOURCE == "local":
        return _load_local_presets()

    if FRONTEND_CONFIG_SOURCE == "backend":
        return _load_backend_presets()

    try:
        return _load_backend_presets()
    except (httpx.HTTPError, ValueError, TypeError):
        # 백엔드가 아직 떠 있지 않은 개발 상황에서는 로컬 파일로 화면을 구성한다.
        return _load_local_presets()


def _format_options_from_presets(
    raw_presets: list[dict[str, object]],
) -> dict[str, dict[str, object]]:
    options = {}

    for preset in raw_presets:
        preset_id = str(preset["id"])
        details = [
            {
                "id": str(detail["id"]),
                "label": str(detail["label"]),
                "size": (int(detail["width"]), int(detail["height"])),
            }
            for detail in preset.get("details", [])
        ]
        options[str(preset["label"])] = {
            "value": preset_id,
            # 상세 유형은 백엔드와 같은 presets.json을 기준으로 맞춘다.
            "details": details,
        }

    return options


def load_format_options() -> dict[str, dict[str, object]]:
    return _format_options_from_presets(load_presets())


FORMAT_OPTIONS = load_format_options()
CHANNEL_SLUGS = {label: str(option["value"]) for label, option in FORMAT_OPTIONS.items()}


def get_detail_options(format_label: str) -> list[dict[str, object]]:
    return FORMAT_OPTIONS[format_label]["details"]


def get_detail_labels(format_label: str) -> list[str]:
    return [str(detail["label"]) for detail in get_detail_options(format_label)]


def get_detail_size(format_label: str, detail_label: str) -> tuple[int, int]:
    for detail in get_detail_options(format_label):
        if detail["label"] == detail_label:
            return detail["size"]

    return get_detail_options(format_label)[0]["size"]


def get_detail_id(format_label: str, detail_label: str) -> str:
    for detail in get_detail_options(format_label):
        if detail["label"] == detail_label:
            return str(detail["id"])

    return str(get_detail_options(format_label)[0]["id"])


def format_size_label(size: tuple[int, int]) -> str:
    return f"{size[0]} x {size[1]}"


def get_channel_asset_path(format_label: str) -> Path:
    preset_id = str(FORMAT_OPTIONS[format_label]["value"])
    return CHANNEL_ASSET_DIR / f"{preset_id}.png"


def get_existing_channel_asset_path(format_label: str) -> Path | None:
    asset_path = get_channel_asset_path(format_label)
    if asset_path.exists():
        return asset_path

    return None
