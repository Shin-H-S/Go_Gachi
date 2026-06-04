from io import BytesIO

from PIL import Image

from frontend.core.config import get_detail_size
from frontend.media.image_common import fit_image_contain


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


