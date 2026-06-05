from io import BytesIO

from PIL import Image, ImageChops

from frontend.media import preview_canvas


def _make_exif_oriented_jpeg(size: tuple[int, int], orientation: int) -> bytes:
    image = Image.new("RGB", size, "#d71920")
    exif = Image.Exif()
    exif[274] = orientation

    output = BytesIO()
    image.save(output, format="JPEG", exif=exif)
    return output.getvalue()


def _foreground_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    background = Image.new("RGB", image.size, "#fbfaf4")
    bbox = ImageChops.difference(image.convert("RGB"), background).getbbox()
    assert bbox is not None
    return bbox


def test_preview_canvas_applies_exif_orientation(monkeypatch) -> None:
    monkeypatch.setattr(preview_canvas, "get_detail_size", lambda *_args: (120, 120))
    image_bytes = _make_exif_oriented_jpeg((80, 40), orientation=6)

    preview_bytes = preview_canvas.make_preview_canvas(
        image_bytes,
        format_label="test",
        detail_label="test",
    )

    preview = Image.open(BytesIO(preview_bytes))
    left, top, right, bottom = _foreground_bbox(preview)
    foreground_width = right - left
    foreground_height = bottom - top

    assert foreground_width == 40
    assert foreground_height == 80
    assert foreground_height > foreground_width
