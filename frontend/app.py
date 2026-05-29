import base64
import json
import os
import time
from io import BytesIO
from pathlib import Path

import httpx
import streamlit as st
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

load_dotenv(Path(__file__).with_name(".env"))
BACKEND_URL = os.getenv("BACKEND_URL", "").rstrip("/")
CONFIG_PRESETS_PATH = Path(__file__).resolve().parents[1] / "config" / "presets.json"


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


st.set_page_config(
    page_title="Cafe Ad Maker",
    page_icon="CA",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def add_css() -> None:
    st.markdown(
        """
        <style>
            :root {
                --paper: #f8f7f2;
                --panel: #fffdf8;
                --ink: #202725;
                --muted: #66716d;
                --line: #dfded6;
                --teal: #0f8f7f;
                --teal-dark: #087163;
            }

            html,
            body,
            .stApp,
            [data-testid="stAppViewContainer"] {
                color-scheme: light;
            }

            .stApp {
                background: linear-gradient(180deg, #f4f1e9 0%, #fbfaf4 48%, #f1f7f5 100%);
                color: var(--ink);
            }

            .main .block-container {
                max-width: 1360px;
                padding: 24px 28px 40px;
            }

            [data-testid="stHeader"] {
                background: transparent;
            }

            h1, h2, h3, p {
                letter-spacing: 0;
            }

            .topbar {
                padding-bottom: 18px;
                border-bottom: 1px solid rgba(32, 39, 37, 0.12);
                margin-bottom: 20px;
            }

            .brand-kicker {
                color: var(--teal-dark);
                font-size: 13px;
                font-weight: 900;
                margin: 0 0 8px;
            }

            .title {
                color: var(--ink);
                font-size: clamp(36px, 5vw, 62px);
                line-height: 1.02;
                font-weight: 950;
                margin: 0;
            }

            .section-label {
                color: #3a4240;
                font-size: 14px;
                font-weight: 900;
                margin: 0 0 8px;
            }

            .small-note {
                color: var(--muted);
                font-size: 13px;
                line-height: 1.55;
                margin: 0 0 12px;
            }

            .format-readout {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                border: 1px solid rgba(32, 39, 37, 0.12);
                border-radius: 8px;
                background: #f5f4ee;
                padding: 12px 14px;
                margin: 6px 0 14px;
                color: #29312f;
                font-size: 13px;
                font-weight: 800;
            }

            .format-readout .channel-name {
                color: var(--ink);
                font-size: 17px;
                font-weight: 950;
                line-height: 1.2;
            }

            .format-readout .format-size {
                color: var(--ink);
                font-size: 18px;
                font-weight: 950;
                line-height: 1;
                white-space: nowrap;
            }

            .format-readout strong,
            .format-readout small {
                display: block;
            }

            .format-readout small {
                color: var(--muted);
                font-size: 12px;
                font-weight: 700;
                margin-top: 4px;
            }

            .detail-choice-label {
                color: #3a4240;
                font-size: 14px;
                font-weight: 900;
                margin: 0 0 8px;
            }

            .st-key-left-upload-section,
            .st-key-left-channel-section,
            .st-key-left-type-section,
            .st-key-left-prompt-section {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1px solid rgba(32, 39, 37, 0.14) !important;
                border-radius: 8px !important;
                box-shadow: 0 10px 22px rgba(44, 47, 42, 0.055);
            }

            .st-key-left-upload-section > div,
            .st-key-left-channel-section > div,
            .st-key-left-type-section > div,
            .st-key-left-prompt-section > div,
            .st-key-left-upload-section [data-testid="stVerticalBlockBorderWrapper"],
            .st-key-left-channel-section [data-testid="stVerticalBlockBorderWrapper"],
            .st-key-left-type-section [data-testid="stVerticalBlockBorderWrapper"],
            .st-key-left-prompt-section [data-testid="stVerticalBlockBorderWrapper"],
            .st-key-left-upload-section [data-testid="stVerticalBlock"],
            .st-key-left-channel-section [data-testid="stVerticalBlock"],
            .st-key-left-type-section [data-testid="stVerticalBlock"],
            .st-key-left-prompt-section [data-testid="stVerticalBlock"] {
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 0 !important;
                box-shadow: none !important;
            }

            .preview-shell {
                height: 620px;
                border: 1px solid rgba(32, 39, 37, 0.13);
                border-radius: 8px;
                background:
                    linear-gradient(45deg, rgba(32,39,37,0.035) 25%, transparent 25%),
                    linear-gradient(-45deg, rgba(32,39,37,0.035) 25%, transparent 25%),
                    linear-gradient(45deg, transparent 75%, rgba(32,39,37,0.035) 75%),
                    linear-gradient(-45deg, transparent 75%, rgba(32,39,37,0.035) 75%),
                    #fbfaf4;
                background-size: 28px 28px;
                background-position: 0 0, 0 14px, 14px -14px, -14px 0;
                padding: 18px;
                box-sizing: border-box;
                overflow: hidden;
            }

            .result-caption {
                display: flex;
                justify-content: space-between;
                gap: 12px;
                color: #5d6764;
                font-size: 13px;
                font-weight: 800;
                margin: 0 0 10px;
            }

            .empty-guide {
                display: flex;
                height: calc(100% - 28px);
                align-items: center;
                justify-content: center;
                text-align: center;
                color: #5d6764;
                font-size: 18px;
                font-weight: 900;
                line-height: 1.65;
            }

            .loading-state {
                display: flex;
                height: calc(100% - 28px);
                align-items: flex-start;
                justify-content: center;
                padding-top: 150px;
                box-sizing: border-box;
                text-align: center;
            }

            .loading-panel {
                display: inline-flex;
                flex-direction: column;
                align-items: center;
                gap: 16px;
                color: #4d5960;
                font-size: 18px;
                font-weight: 900;
                line-height: 1.55;
            }

            .loading-spinner {
                width: 54px;
                height: 54px;
                border-radius: 999px;
                border: 6px solid rgba(108, 94, 214, 0.14);
                border-top-color: #5145c6;
                border-right-color: #a790ff;
                animation: spin 0.85s linear infinite;
            }

            .preview-image-frame {
                height: calc(100% - 28px);
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: hidden;
            }

            .preview-image-frame img {
                display: block;
                max-width: 100%;
                max-height: 100%;
                width: auto;
                height: auto;
                object-fit: contain;
                border-radius: 8px;
                border: 1px solid rgba(32, 39, 37, 0.12);
                box-sizing: border-box;
            }

            @keyframes spin {
                from {
                    transform: rotate(0deg);
                }
                to {
                    transform: rotate(360deg);
                }
            }

            .stTextArea textarea,
            div[data-testid="stTextArea"] textarea,
            textarea {
                border-radius: 8px;
                background: #f5f4ee !important;
                color: var(--ink) !important;
                -webkit-text-fill-color: var(--ink) !important;
                caret-color: var(--teal);
            }

            .stTextArea textarea::placeholder,
            div[data-testid="stTextArea"] textarea::placeholder,
            textarea::placeholder {
                color: #7a8793 !important;
                -webkit-text-fill-color: #7a8793 !important;
                opacity: 1 !important;
            }

            div[data-testid="stButton"] button,
            div[data-testid="stDownloadButton"] button,
            button[data-testid^="stBaseButton"] {
                min-height: 48px;
                border-radius: 8px;
                border: 1px solid rgba(32, 39, 37, 0.14) !important;
                background: linear-gradient(180deg, #f5f4ee 0%, #e8e6de 100%) !important;
                color: #29312f !important;
                -webkit-text-fill-color: #29312f !important;
                font-weight: 900;
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.75), 0 8px 18px rgba(44, 47, 42, 0.08);
            }

            div[data-testid="stButton"] button *,
            div[data-testid="stDownloadButton"] button *,
            button[data-testid^="stBaseButton"] * {
                color: inherit !important;
                -webkit-text-fill-color: inherit !important;
            }

            div[data-testid="stButton"] button[kind="primary"],
            div[data-testid="stButton"] button[data-testid="stBaseButton-primary"] {
                min-height: 48px;
                border-radius: 8px;
                border: 1px solid var(--teal-dark) !important;
                background: var(--teal) !important;
                color: white !important;
                -webkit-text-fill-color: white !important;
                font-weight: 900;
                box-shadow: 0 12px 24px rgba(15, 143, 127, 0.22);
            }

            div[data-testid="stButton"] button[kind="primary"] *,
            div[data-testid="stButton"] button[data-testid="stBaseButton-primary"] * {
                color: white !important;
                -webkit-text-fill-color: white !important;
            }

            div[data-testid="stButton"] button[kind="primary"]:hover,
            div[data-testid="stButton"] button[data-testid="stBaseButton-primary"]:hover {
                border: 1px solid var(--teal-dark) !important;
                background: var(--teal-dark) !important;
                color: white !important;
                -webkit-text-fill-color: white !important;
            }

            div[data-testid="stElementContainer"]:has(.generate-button-marker)
                + div[data-testid="stElementContainer"] button,
            div[data-testid="stElementContainer"]:has(.generate-button-marker)
                + div[data-testid="stButton"] button {
                min-height: 58px !important;
                border-radius: 999px !important;
                border: 1px solid #0f4cbd !important;
                background:
                    linear-gradient(90deg, #062d70 0%, #0c4db8 58%, #76b8ff 100%)
                    !important;
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
                font-size: 18px !important;
                font-weight: 950 !important;
                box-shadow: 0 12px 24px rgba(20, 79, 189, 0.24);
            }

            div[data-testid="stElementContainer"]:has(.generate-button-marker)
                + div[data-testid="stElementContainer"] button *,
            div[data-testid="stElementContainer"]:has(.generate-button-marker)
                + div[data-testid="stButton"] button * {
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
                font-size: 18px !important;
                font-weight: 950 !important;
            }

            div[data-testid="stElementContainer"]:has(.generate-button-marker)
                + div[data-testid="stElementContainer"] button:hover,
            div[data-testid="stElementContainer"]:has(.generate-button-marker)
                + div[data-testid="stButton"] button:hover {
                border: 1px solid #0b3e9e !important;
                background:
                    linear-gradient(90deg, #05275f 0%, #0a45a5 58%, #65aaf4 100%)
                    !important;
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
            }

            .tool-row {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 8px;
                margin-top: 10px;
            }

            .tool-row .stButton > button,
            .tool-row .stDownloadButton > button {
                min-height: 58px;
                border: 1px solid rgba(32, 39, 37, 0.12);
                border-radius: 4px;
                background: linear-gradient(180deg, #f5f4ee 0%, #e8e6de 100%) !important;
                color: #29312f !important;
                -webkit-text-fill-color: #29312f !important;
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.75), 0 8px 18px rgba(44, 47, 42, 0.08);
                font-size: 28px;
                font-weight: 900;
            }

            .tool-row .stButton > button:hover,
            .tool-row .stDownloadButton > button:hover {
                border: 1px solid rgba(15, 143, 127, 0.28);
                background: linear-gradient(180deg, #ffffff 0%, #d7e5e1 100%) !important;
                color: #0b6f63 !important;
                -webkit-text-fill-color: #0b6f63 !important;
            }

            div[data-testid="stFileUploader"] section {
                border: 1px dashed rgba(15, 143, 127, 0.42);
                border-radius: 8px;
                background: #f5f4ee !important;
                color: var(--ink) !important;
            }

            div[data-testid="stFileUploaderFile"],
            div[data-testid="stFileUploaderFile"] > div,
            div[data-testid="stFileUploaderDropzone"] {
                background: #f5f4ee !important;
                color: var(--ink) !important;
            }

            div[data-testid="stFileUploader"] section *,
            div[data-testid="stFileUploaderFile"] *,
            div[data-testid="stFileUploaderDropzone"] * {
                color: var(--ink) !important;
                -webkit-text-fill-color: var(--ink) !important;
            }

            div[data-testid="stFileUploader"] button {
                background: #ffffff !important;
                color: var(--ink) !important;
                -webkit-text-fill-color: var(--ink) !important;
                border: 1px solid rgba(32, 39, 37, 0.14) !important;
            }

            div[role="radiogroup"] {
                gap: 6px;
            }

            .channel-tabs {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 8px;
                width: 100%;
                margin: 0 0 14px;
            }

            .channel-tab {
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 84px;
                border: 1px solid rgba(32, 39, 37, 0.14);
                border-radius: 8px;
                background: #f5f4ee;
                color: var(--ink) !important;
                -webkit-text-fill-color: var(--ink) !important;
                font-size: 18px;
                font-weight: 900;
                line-height: 1.2;
                text-align: center;
                text-decoration: none !important;
                box-sizing: border-box;
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.75), 0 8px 18px rgba(44, 47, 42, 0.08);
            }

            .channel-tab:hover {
                border-color: rgba(15, 143, 127, 0.45);
                background: #eef8f5;
                color: var(--ink) !important;
                -webkit-text-fill-color: var(--ink) !important;
                text-decoration: none !important;
            }

            .channel-tab.is-active {
                border-color: var(--teal-dark);
                background: var(--teal);
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
            }

            div[data-testid="stElementContainer"]:has(.channel-button-marker)
                + div[data-testid="stHorizontalBlock"] {
                width: 100% !important;
            }

            div[data-testid="stElementContainer"]:has(.channel-button-marker)
                + div[data-testid="stHorizontalBlock"] div[data-testid="column"] {
                min-width: 0 !important;
            }

            div[data-testid="stElementContainer"]:has(.channel-button-marker)
                + div[data-testid="stHorizontalBlock"] button {
                min-height: 84px !important;
                width: 100% !important;
                font-size: 18px !important;
                font-weight: 900 !important;
                line-height: 1.2 !important;
            }

            div[data-testid="stElementContainer"]:has(.channel-button-marker)
                + div[data-testid="stHorizontalBlock"] button * {
                font-size: 18px !important;
                font-weight: 900 !important;
                line-height: 1.2 !important;
            }

            div[data-testid="stSegmentedControl"] {
                width: 100% !important;
                max-width: none !important;
            }

            div[data-testid="stSegmentedControl"] > div,
            div[data-testid="stSegmentedControl"] [data-baseweb="button-group"],
            div[data-testid="stSegmentedControl"] [role="group"],
            div[data-testid="stSegmentedControl"] div:has(> button) {
                display: grid !important;
                grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
                width: 100% !important;
                max-width: none !important;
                gap: 8px !important;
            }

            div[data-testid="stSegmentedControl"] button {
                width: 100% !important;
                min-width: 0 !important;
                max-width: none !important;
                flex: 1 1 0 !important;
                min-height: 84px;
                border-radius: 8px !important;
                border: 1px solid rgba(32, 39, 37, 0.14) !important;
                background: #f5f4ee !important;
                color: var(--ink) !important;
                -webkit-text-fill-color: var(--ink) !important;
                font-size: 18px !important;
                font-weight: 900 !important;
                line-height: 1.2 !important;
            }

            div[data-testid="stSegmentedControl"] button[aria-pressed="true"],
            div[data-testid="stSegmentedControl"] button[data-selected="true"] {
                border-color: rgba(15, 143, 127, 0.45) !important;
                background: #eef8f5 !important;
                color: var(--ink) !important;
                -webkit-text-fill-color: var(--ink) !important;
            }

            div[data-testid="stSegmentedControl"] button * {
                color: var(--ink) !important;
                -webkit-text-fill-color: var(--ink) !important;
                font-size: 18px !important;
                font-weight: 900 !important;
                line-height: 1.2 !important;
            }

            div[data-testid="stRadio"] label,
            div[role="radiogroup"] label {
                border: 1px solid rgba(32, 39, 37, 0.12);
                border-radius: 8px;
                background: #f5f4ee !important;
                color: var(--ink) !important;
                padding: 8px 10px;
                min-height: 40px;
            }

            div[data-testid="stRadio"] label *,
            div[role="radiogroup"] label *,
            div[role="radiogroup"] label p {
                color: var(--ink) !important;
                -webkit-text-fill-color: var(--ink) !important;
            }

            [data-testid="stImage"] img {
                border-radius: 8px;
                border: 1px solid rgba(32, 39, 37, 0.12);
            }

            @media (max-width: 900px) {
                .main .block-container {
                    padding: 18px 14px 32px;
                }

                .preview-shell {
                    height: 360px;
                }

            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_names = ["malgunbd.ttf", "malgun.ttf"] if bold else ["malgun.ttf", "malgunbd.ttf"]
    candidates = [Path("C:/Windows/Fonts") / name for name in font_names]

    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)

    return ImageFont.load_default()


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def draw_gradient(image: Image.Image, start_hex: str, end_hex: str) -> None:
    width, height = image.size
    start = hex_to_rgb(start_hex)
    end = hex_to_rgb(end_hex)
    draw = ImageDraw.Draw(image)

    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(
            round(start[channel] * (1 - ratio) + end[channel] * ratio)
            for channel in range(3)
        )
        draw.line([(0, y), (width, y)], fill=color)


def rounded_paste(
    base: Image.Image,
    overlay: Image.Image,
    box: tuple[int, int],
    radius: int,
) -> None:
    overlay = overlay.convert("RGBA")
    mask = Image.new("L", overlay.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, overlay.width, overlay.height), radius=radius, fill=255)
    base.paste(overlay, box, mask)


def fit_image_cover(source: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    image = source.convert("RGB")
    return ImageOps.fit(image, target_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def fit_image_contain(source: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    image = source.convert("RGB")
    image.thumbnail(target_size, Image.Resampling.LANCZOS)
    return image


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


def make_preview_canvas(image_bytes: bytes, format_label: str, detail_label: str) -> bytes:
    target_size = get_detail_size(format_label, detail_label)
    canvas = Image.new("RGB", target_size, "#fbfaf4")
    image = fit_image_contain(Image.open(BytesIO(image_bytes)), target_size)
    x = (target_size[0] - image.width) // 2
    y = (target_size[1] - image.height) // 2
    canvas.paste(image, (x, y))

    output = BytesIO()
    canvas.save(output, format="PNG", optimize=True)
    return output.getvalue()


def wrap_text_by_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    clean_text = " ".join(text.strip().split())
    if not clean_text:
        return []

    lines: list[str] = []
    current = ""
    for char in clean_text:
        candidate = current + char
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = char
            if len(lines) >= max_lines:
                break

    if current and len(lines) < max_lines:
        lines.append(current)

    return lines


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: str,
    max_width: int,
    line_gap: int,
    max_lines: int,
) -> int:
    x, y = xy
    lines = wrap_text_by_width(draw, text, font, max_width, max_lines)
    for line in lines:
        draw.text((x, y), line, fill=fill, font=font)
        bbox = draw.textbbox((x, y), line, font=font)
        y += bbox[3] - bbox[1] + line_gap
    return y


def create_mock_banner(
    image_bytes: bytes,
    prompt: str,
    format_label: str,
    detail_label: str,
) -> bytes:
    width, height = get_detail_size(format_label, detail_label)
    scale = min(width, height) / 1080

    background = Image.new("RGB", (width, height), "#f8f7f2")
    draw_gradient(background, "#f8f7f2", "#e8f3ef")
    banner = background.convert("RGBA")

    margin = int(width * 0.075)
    photo_source = Image.open(BytesIO(image_bytes))
    photo_box = (int(width * 0.25), int(height * 0.34), int(width * 0.50), int(height * 0.54))
    px, py, pw, ph = photo_box

    shadow = Image.new("RGBA", (pw + 60, ph + 60), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (30, 30, pw + 30, ph + 30),
        radius=int(34 * scale),
        fill=(35, 42, 39, 46),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(int(18 * scale)))
    banner.paste(shadow, (px - 30, py - 30), shadow)

    photo = fit_image_cover(photo_source, (pw, ph))
    rounded_paste(banner, photo, (px, py), radius=int(30 * scale))

    draw = ImageDraw.Draw(banner)
    draw.rounded_rectangle(
        (px, py, px + pw, py + ph),
        radius=int(30 * scale),
        outline=(255, 255, 255, 210),
        width=max(3, int(5 * scale)),
    )

    title_font = load_font(max(34, int(58 * scale)), bold=True)
    body_font = load_font(max(22, int(34 * scale)), bold=False)

    text_x = margin
    text_y = int(height * 0.10)
    text_width = int(width * 0.78)
    cursor_y = draw_wrapped_text(
        draw,
        (text_x, text_y),
        "프롬프트 기반 미리보기",
        title_font,
        "#202725",
        text_width,
        int(8 * scale),
        2,
    )
    cursor_y += int(18 * scale)
    draw_wrapped_text(
        draw,
        (text_x, cursor_y),
        prompt,
        body_font,
        "#202725",
        text_width,
        int(8 * scale),
        3,
    )

    draw.text(
        (margin, height - int(42 * scale)),
        "CAFE AD MAKER",
        fill=(32, 39, 37, 128),
        font=load_font(max(16, int(22 * scale)), bold=True),
    )

    output = BytesIO()
    banner.convert("RGB").save(output, format="PNG", optimize=True)
    return output.getvalue()


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


def bytes_to_data_url(image_bytes: bytes, mime_type: str = "image/png") -> str:
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def build_feedback(prompt: str, detail_label: str) -> str:
    return f"광고 유형: {detail_label}\n{prompt.strip()}"


def request_backend(uploaded_file, prompt: str, format_label: str, detail_label: str) -> bytes:
    if not BACKEND_URL:
        raise RuntimeError("BACKEND_URL이 설정되어 있지 않습니다.")

    target_size = get_detail_size(format_label, detail_label)
    payload = {
        "imageDataUrl": file_to_data_url(uploaded_file),
        "presetId": FORMAT_OPTIONS[format_label]["value"],
        "feedback": build_feedback(prompt, detail_label),
        "targetWidth": target_size[0],
        "targetHeight": target_size[1],
    }

    response = httpx.post(f"{BACKEND_URL}/api/generate", json=payload, timeout=90)
    response.raise_for_status()
    data = response.json()
    image_data_url = data.get("imageDataUrl")
    if not image_data_url:
        raise ValueError("백엔드 응답에 imageDataUrl이 없습니다.")

    return data_url_to_bytes(image_data_url)


def compact_html(html: str) -> str:
    return " ".join(line.strip() for line in html.strip().splitlines() if line.strip())


def render_preview_shell(
    format_label: str,
    body_html: str,
    detail_label: str | None = None,
) -> None:
    body = compact_html(body_html)
    caption = f"{format_label} · {detail_label}" if detail_label else format_label
    size_label = (
        format_size_label(get_detail_size(format_label, detail_label)) if detail_label else ""
    )
    st.markdown(
        (
            '<div class="preview-shell">'
            '<div class="result-caption">'
            f"<span>{caption}</span>"
            f"<span>{size_label}</span>"
            "</div>"
            f"{body}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_image_preview(
    image_bytes: bytes,
    format_label: str,
    detail_label: str | None = None,
) -> None:
    preview_bytes = make_preview_canvas(image_bytes, format_label, detail_label)
    preview_src = bytes_to_data_url(preview_bytes)
    render_preview_shell(
        format_label,
        f"""
        <div class="preview-image-frame">
            <img src="{preview_src}" alt="미리보기 이미지" />
        </div>
        """,
        detail_label,
    )


def get_selected_channel() -> str:
    selected_label = st.session_state.get("selected_channel", "인스타그램")
    if selected_label not in FORMAT_OPTIONS:
        selected_label = "인스타그램"
        st.session_state["selected_channel"] = selected_label

    return selected_label


def render_channel_tabs(selected_label: str) -> None:
    st.markdown('<div class="channel-button-marker"></div>', unsafe_allow_html=True)
    columns = st.columns(3, gap="small")

    for column, label in zip(columns, FORMAT_OPTIONS.keys(), strict=True):
        with column:
            clicked = st.button(
                label,
                key=f"channel_{CHANNEL_SLUGS[label]}",
                type="primary" if label == selected_label else "secondary",
                use_container_width=True,
            )
            if clicked and label != selected_label:
                st.session_state["selected_channel"] = label
                st.rerun()


def render_header() -> None:
    st.markdown(
        """
        <div class="topbar">
            <p class="brand-kicker">GO-GACHI CAFE AD MAKER V1</p>
            <h1 class="title">카페 메뉴 광고 이미지 제작</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )


add_css()
render_header()

left_col, right_col = st.columns([0.32, 0.68], gap="large")

with left_col:
    with st.container(border=True, key="left-upload-section"):
        st.markdown(
            """
            <p class="section-label">메뉴 사진 업로드</p>
            """,
            unsafe_allow_html=True,
        )

        uploaded_file = st.file_uploader(
            "메뉴 사진 업로드",
            type=["jpg", "jpeg", "png", "webp"],
            help="JPG, PNG, WEBP 파일을 업로드할 수 있습니다.",
            label_visibility="collapsed",
        )

    with st.container(border=True, key="left-channel-section"):
        st.markdown('<p class="section-label">광고 채널 선택</p>', unsafe_allow_html=True)
        format_label = get_selected_channel()
        render_channel_tabs(format_label)

    with st.container(border=True, key="left-type-section"):
        detail_options = get_detail_labels(format_label)
        st.markdown('<p class="detail-choice-label">광고 유형 선택</p>', unsafe_allow_html=True)
        detail_label = st.radio(
            "광고 유형 선택",
            options=detail_options,
            horizontal=False,
            label_visibility="collapsed",
            key=f"detail_{FORMAT_OPTIONS[format_label]['value']}",
        )
        format_label_html = format_size_label(get_detail_size(format_label, detail_label))
        st.markdown(
            f"""
            <div class="format-readout">
                <span>
                    <strong class="channel-name">{format_label}</strong>
                    <small>{detail_label}</small>
                </span>
                <span class="format-size">{format_label_html}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.container(border=True, key="left-prompt-section"):
        st.markdown('<p class="section-label">프롬프트</p>', unsafe_allow_html=True)
        prompt = st.text_area(
            "프롬프트",
            placeholder=(
                "예:\n"
                "제품을 크게 중앙에 배치해줘\n"
                "따뜻한 색감으로 만들어줘\n"
                "미니멀하고 프리미엄한 배경으로"
            ),
            height=150,
            label_visibility="collapsed",
        )

        st.markdown('<div class="generate-button-marker"></div>', unsafe_allow_html=True)
        generate = st.button("✦ 이미지 만들기", use_container_width=True, type="primary")

        st.markdown('<div class="tool-row">', unsafe_allow_html=True)
        undo_col, redo_col, save_col = st.columns(3, gap="small")
        with undo_col:
            undo_clicked = st.button("↶", help="되돌리기", use_container_width=True)
        with redo_col:
            redo_clicked = st.button("↷", help="다시 실행", use_container_width=True)
        with save_col:
            if "result_bytes" in st.session_state:
                st.download_button(
                    "💾",
                    data=st.session_state["result_bytes"],
                    file_name="cafe_ad_maker_result.png",
                    mime="image/png",
                    help="저장",
                    use_container_width=True,
                )
            else:
                save_clicked = st.button("💾", help="저장", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if undo_clicked:
        st.info("되돌릴 이전 결과가 아직 없습니다.")
    if redo_clicked:
        st.info("다시 실행할 다음 결과가 아직 없습니다.")
    if "result_bytes" not in st.session_state and "save_clicked" in locals() and save_clicked:
        st.info("저장할 결과 이미지를 먼저 만들어주세요.")

is_generating = bool(generate and uploaded_file and prompt.strip())

if is_generating:
    st.markdown(
        """
        <style>
            div[role="radiogroup"] label:not(:has(input:checked)) {
                opacity: 0.34;
                pointer-events: none;
            }

            div[role="radiogroup"] label:has(input:checked) {
                opacity: 1;
            }

            .channel-tab:not(.is-active),
            div[data-testid="stSegmentedControl"]
                button:not([aria-pressed="true"]):not([data-selected="true"]) {
                opacity: 0.34;
                pointer-events: none;
            }

            div[data-testid="stElementContainer"]:has(.channel-button-marker)
                + div[data-testid="stHorizontalBlock"]
                button[data-testid="stBaseButton-secondary"] {
                opacity: 0.34;
                pointer-events: none;
            }

            .channel-tab.is-active,
            div[data-testid="stSegmentedControl"] button[aria-pressed="true"],
            div[data-testid="stSegmentedControl"] button[data-selected="true"] {
                opacity: 1;
            }

            div[data-testid="stElementContainer"]:has(.channel-button-marker)
                + div[data-testid="stHorizontalBlock"] button[data-testid="stBaseButton-primary"] {
                opacity: 1;
            }

            div[data-testid="stButton"] button[kind="primary"],
            div[data-testid="stButton"] button[data-testid="stBaseButton-primary"] {
                background: #aab7b3 !important;
                color: #eef3f1 !important;
                -webkit-text-fill-color: #eef3f1 !important;
                box-shadow: none !important;
                cursor: not-allowed !important;
                pointer-events: none;
            }

            div[data-testid="stButton"] button[kind="primary"] *,
            div[data-testid="stButton"] button[data-testid="stBaseButton-primary"] * {
                color: #eef3f1 !important;
                -webkit-text-fill-color: #eef3f1 !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

with right_col:
    if is_generating:
        render_preview_shell(
            format_label,
            """
            <div class="loading-state">
                <div class="loading-panel">
                    <div class="loading-spinner"></div>
                    <div>제작 중입니다. 잠시만 기다려주세요.</div>
                </div>
            </div>
            """,
            detail_label,
        )
    elif uploaded_file and "result_bytes" not in st.session_state:
        render_image_preview(uploaded_file.getvalue(), format_label, detail_label)
    elif "result_bytes" in st.session_state:
        render_image_preview(st.session_state["result_bytes"], format_label, detail_label)
        st.download_button(
            "이미지 다운로드",
            data=st.session_state["result_bytes"],
            file_name="cafe_ad_maker_result.png",
            mime="image/png",
            use_container_width=True,
        )
    else:
        render_preview_shell(
            format_label,
            """
            <div class="empty-guide">
                단순한 배경에서, 광고에 사용할 각도로 촬영한 이미지를 올려주세요.
            </div>
            """,
            detail_label,
        )

if generate:
    if not uploaded_file:
        st.warning("메뉴 사진을 먼저 업로드해주세요.")
    elif not prompt.strip():
        st.warning("프롬프트를 입력해주세요.")
    else:
        try:
            time.sleep(1.2)
            if BACKEND_URL:
                result_bytes = request_backend(
                    uploaded_file,
                    prompt.strip(),
                    format_label,
                    detail_label,
                )
            else:
                result_bytes = create_mock_banner(
                    image_bytes=uploaded_file.getvalue(),
                    prompt=build_feedback(prompt.strip(), detail_label),
                    format_label=format_label,
                    detail_label=detail_label,
                )
            st.session_state["result_bytes"] = result_bytes
            st.rerun()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text
            st.error(f"백엔드 생성 요청에 실패했습니다. ({exc.response.status_code}) {detail}")
        except httpx.HTTPError as exc:
            st.error(f"백엔드에 연결할 수 없습니다: {exc}")
        except Exception as exc:
            st.error(f"이미지 생성 중 오류가 발생했습니다: {exc}")
