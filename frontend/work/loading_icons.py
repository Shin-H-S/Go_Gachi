from functools import cache
from pathlib import Path

from frontend.media.image_data import bytes_to_data_url

_LOADING_ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "loading"

LOADING_ICON_FILES = (
    "1_mango_passionfruit_ade.png", "2_strawberry_cream_cake.png",
    "3_hot_americano.png", "4_iced_milk_tea.png", "5_plain_croissant.png",
    "6_caramel_macchiato.png", "7_hot_chocolate.png",
    "8_blueberry_basque_cheesecake.png", "9_einspanner.png",
    "10_sweet_potato_latte.png", "11_ice_cream_croffle.png",
    "12_iced_americano.png", "13_tiramisu.png", "14_matcha_latte.png",
    "15_affogato.png", "16_grapefruit_honey_black_tea.png", "17_fat_macaron.png",
)


@cache
def loading_icon_data_url(filename: str) -> str:
    return bytes_to_data_url((_LOADING_ASSET_DIR / filename).read_bytes())
