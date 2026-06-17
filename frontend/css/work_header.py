from frontend.css.work_header_parts.auth import WORK_HEADER_AUTH_CSS
from frontend.css.work_header_parts.download import WORK_HEADER_DOWNLOAD_CSS
from frontend.css.work_header_parts.profile import WORK_HEADER_PROFILE_CSS
from frontend.css.work_header_parts.responsive import WORK_HEADER_RESPONSIVE_CSS

WORK_HEADER_CSS = "\n".join(
    [
        WORK_HEADER_PROFILE_CSS,
        WORK_HEADER_AUTH_CSS,
        WORK_HEADER_DOWNLOAD_CSS,
        WORK_HEADER_RESPONSIVE_CSS,
    ]
)
