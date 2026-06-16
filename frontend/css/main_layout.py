from frontend.css.main_layout_parts.hero import MAIN_LAYOUT_HERO_CSS
from frontend.css.main_layout_parts.navigation import MAIN_LAYOUT_NAVIGATION_CSS
from frontend.css.main_layout_parts.shell import MAIN_LAYOUT_SHELL_CSS

MAIN_LAYOUT_CSS = "\n".join(
    (
        MAIN_LAYOUT_SHELL_CSS,
        MAIN_LAYOUT_NAVIGATION_CSS,
        MAIN_LAYOUT_HERO_CSS,
    )
)
