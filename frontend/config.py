import json
from pathlib import Path

CONFIG_PRESETS_PATH = Path(__file__).resolve().parents[1] / "config" / "presets.json"
CHANNEL_ASSET_DIR = Path(__file__).resolve().parent / "assets"


def load_format_options() -> dict[str, dict[str, object]]:
    raw_presets = json.loads(CONFIG_PRESETS_PATH.read_text(encoding="utf-8"))
    options = {}

    for preset in raw_presets:
        preset_id = str(preset["id"])
        fallback_detail = {
            "id": "default",
            "label": str(preset["label"]),
            "size": (int(preset["width"]), int(preset["height"])),
        }
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
            "details": details or [fallback_detail],
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
