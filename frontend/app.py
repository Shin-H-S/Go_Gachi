import base64
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

FORMAT_OPTIONS = {
    "인스타 광고": {
        "value": "instagram_square",
        "label": "1080 x 1080",
        "size": (1080, 1080),
    },
    "배민 광고": {
        "value": "baemin_ad",
        "label": "1280 x 560",
        "size": (1280, 560),
    },
    "당근 광고": {
        "value": "daangn_post",
        "label": "1200 x 900",
        "size": (1200, 900),
    },
}


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
                background: #ffffff;
                padding: 12px 14px;
                margin: 6px 0 14px;
                color: #29312f;
                font-size: 13px;
                font-weight: 800;
            }

            .preview-shell {
                min-height: 620px;
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
                min-height: 540px;
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
                min-height: 540px;
                align-items: flex-start;
                justify-content: center;
                padding-top: 150px;
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

            @keyframes spin {
                from {
                    transform: rotate(0deg);
                }
                to {
                    transform: rotate(360deg);
                }
            }

            .stTextArea textarea {
                border-radius: 8px;
            }

            .stButton > button,
            .stDownloadButton > button {
                min-height: 48px;
                border-radius: 8px;
                border: 0;
                background: var(--teal);
                color: white;
                font-weight: 900;
                box-shadow: 0 12px 24px rgba(15, 143, 127, 0.22);
            }

            .stButton > button:hover,
            .stDownloadButton > button:hover {
                border: 0;
                background: var(--teal-dark);
                color: white;
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
                background: linear-gradient(180deg, #f8f8f4 0%, #deded8 100%);
                color: #29312f;
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.75), 0 8px 18px rgba(44, 47, 42, 0.08);
                font-size: 20px;
                font-weight: 900;
            }

            .tool-row .stButton > button:hover,
            .tool-row .stDownloadButton > button:hover {
                border: 1px solid rgba(15, 143, 127, 0.28);
                background: linear-gradient(180deg, #ffffff 0%, #d7e5e1 100%);
                color: #0b6f63;
            }

            div[data-testid="stFileUploader"] section {
                border: 1px dashed rgba(15, 143, 127, 0.42);
                border-radius: 8px;
                background: #ffffff;
            }

            div[role="radiogroup"] {
                gap: 6px;
            }

            div[role="radiogroup"] label {
                border: 1px solid rgba(32, 39, 37, 0.12);
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.86);
                padding: 8px 10px;
                min-height: 40px;
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
                    min-height: 360px;
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
        color = tuple(round(start[channel] * (1 - ratio) + end[channel] * ratio) for channel in range(3))
        draw.line([(0, y), (width, y)], fill=color)


def rounded_paste(base: Image.Image, overlay: Image.Image, box: tuple[int, int], radius: int) -> None:
    overlay = overlay.convert("RGBA")
    mask = Image.new("L", overlay.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, overlay.width, overlay.height), radius=radius, fill=255)
    base.paste(overlay, box, mask)


def fit_image_cover(source: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    image = ImageOps.exif_transpose(source).convert("RGB")
    return ImageOps.fit(image, target_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


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


def create_mock_banner(image_bytes: bytes, prompt: str, format_label: str) -> bytes:
    width, height = FORMAT_OPTIONS[format_label]["size"]
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
    shadow_draw.rounded_rectangle((30, 30, pw + 30, ph + 30), radius=int(34 * scale), fill=(35, 42, 39, 46))
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


def request_backend(uploaded_file, prompt: str, format_label: str) -> bytes:
    if not BACKEND_URL:
        raise RuntimeError("BACKEND_URL이 설정되어 있지 않습니다.")

    payload = {
        "imageDataUrl": file_to_data_url(uploaded_file),
        "presetId": FORMAT_OPTIONS[format_label]["value"],
        "feedback": prompt,
    }

    response = httpx.post(f"{BACKEND_URL}/api/generate", json=payload, timeout=90)
    response.raise_for_status()
    data = response.json()
    image_data_url = data.get("imageDataUrl")
    if not image_data_url:
        raise ValueError("백엔드 응답에 imageDataUrl이 없습니다.")

    return data_url_to_bytes(image_data_url)


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

    st.markdown('<p class="section-label">광고 채널 선택</p>', unsafe_allow_html=True)
    format_label = st.radio(
        "광고 채널 선택",
        options=list(FORMAT_OPTIONS.keys()),
        horizontal=False,
        label_visibility="collapsed",
    )
    st.markdown(
        f"""
        <div class="format-readout">
            <span>{format_label}</span>
            <span>{FORMAT_OPTIONS[format_label]["label"]}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<p class="section-label">프롬프트</p>', unsafe_allow_html=True)
    prompt = st.text_area(
        "프롬프트",
        placeholder="예:\n제품을 크게 중앙에 배치해줘\n따뜻한 색감으로 만들어줘\n미니멀하고 프리미엄한 배경으로",
        height=150,
        label_visibility="collapsed",
    )

    generate = st.button("이미지 만들기", use_container_width=True, type="primary")

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

            .stButton > button[kind="primary"] {
                background: #aab7b3 !important;
                color: #eef3f1 !important;
                box-shadow: none !important;
                cursor: not-allowed !important;
                pointer-events: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

with right_col:
    if is_generating:
        st.markdown(
            f"""
            <div class="preview-shell">
                <div class="result-caption">
                    <span>{format_label}</span>
                    <span>{FORMAT_OPTIONS[format_label]["label"]}</span>
                </div>
                <div class="loading-state">
                    <div class="loading-panel">
                        <div class="loading-spinner"></div>
                        <div>제작 중입니다. 잠시만 기다려주세요.</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif uploaded_file and "result_bytes" not in st.session_state:
        st.markdown(
            f"""
            <div class="result-caption">
                <span>{format_label}</span>
                <span>{FORMAT_OPTIONS[format_label]["label"]}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.image(uploaded_file, caption="업로드한 사진 미리보기", use_container_width=True)
    elif "result_bytes" in st.session_state:
        st.markdown(
            f"""
            <div class="result-caption">
                <span>{format_label}</span>
                <span>{FORMAT_OPTIONS[format_label]["label"]}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.image(st.session_state["result_bytes"], caption="생성된 홍보 이미지", use_container_width=True)
        st.download_button(
            "이미지 다운로드",
            data=st.session_state["result_bytes"],
            file_name="cafe_ad_maker_result.png",
            mime="image/png",
            use_container_width=True,
        )
    else:
        st.markdown(
            f"""
            <div class="preview-shell">
                <div class="result-caption">
                    <span>{format_label}</span>
                    <span>{FORMAT_OPTIONS[format_label]["label"]}</span>
                </div>
                <div class="empty-guide">
                    단순한 배경에서, 광고에 사용할 각도로 촬영한 이미지를 올려주세요.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
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
                result_bytes = request_backend(uploaded_file, prompt.strip(), format_label)
            else:
                result_bytes = create_mock_banner(
                    image_bytes=uploaded_file.getvalue(),
                    prompt=prompt.strip(),
                    format_label=format_label,
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
