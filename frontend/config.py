import json
from pathlib import Path

CONFIG_PRESETS_PATH = Path(__file__).resolve().parents[1] / "config" / "presets.json"
CHANNEL_ASSET_DIR = Path(__file__).resolve().parent / "assets"


DETAIL_OPTIONS_BY_PRESET_ID = {
    "instagram_square": [
        {"label": "정사각형 피드", "size": (1080, 1080)},
        {"label": "세로형 피드", "size": (1080, 1350)},
        {"label": "스토리 이미지", "size": (1080, 1920)},
    ],
    "baemin_notice": [
        {"label": "단색 배경 이미지", "size": (1280, 960)},
        {"label": "공간 배경 이미지", "size": (1280, 960)},
    ],
    "daangn_post": [
        {"label": "메뉴 이미지", "size": (1080, 1080)},
        {"label": "가게 콘텐츠보드", "size": (1080, 1080)},
        {"label": "사장님 공지 이미지", "size": (1080, 1080)},
        {"label": "홍보 이미지", "size": (1280, 960)},
        {"label": "할인/이벤트 이미지", "size": (1280, 960)},
    ],
}


def load_format_options() -> dict[str, dict[str, object]]:
    raw_presets = json.loads(CONFIG_PRESETS_PATH.read_text(encoding="utf-8"))
    options = {}

    for preset in raw_presets:
        preset_id = str(preset["id"])
        fallback_detail = {
            "label": str(preset["label"]),
            "size": (int(preset["width"]), int(preset["height"])),
        }
        options[str(preset["label"])] = {
            "value": preset_id,
            "details": DETAIL_OPTIONS_BY_PRESET_ID.get(preset_id, [fallback_detail]),
        }

    return options


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
