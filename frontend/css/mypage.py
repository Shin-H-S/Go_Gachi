from frontend.css.mypage_parts.account import MYPAGE_ACCOUNT_CSS
from frontend.css.mypage_parts.cards import MYPAGE_CARDS_CSS
from frontend.css.mypage_parts.layout import MYPAGE_LAYOUT_CSS
from frontend.css.mypage_parts.navigation import MYPAGE_NAVIGATION_CSS

MYPAGE_CSS = "\n".join(
    (
        MYPAGE_LAYOUT_CSS.strip(),
        MYPAGE_NAVIGATION_CSS.strip(),
        MYPAGE_CARDS_CSS.strip(),
        MYPAGE_ACCOUNT_CSS.strip(),
    )
)
