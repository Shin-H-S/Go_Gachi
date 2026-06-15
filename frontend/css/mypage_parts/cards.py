from frontend.css.mypage_parts.card_actions import MYPAGE_CARD_ACTIONS_CSS
from frontend.css.mypage_parts.card_thumbnails import MYPAGE_CARD_THUMBNAILS_CSS

MYPAGE_CARD_LAYOUT_CSS = """
.mypage-card-grid,
.mypage-card-grid-marker {
    margin-top: 8px;
}

.mypage-list-status {
    margin: 2px 0 14px;
    color: #606b67;
    font-size: 13px;
    font-weight: 900;
}

.mypage-pagination-status {
    min-height: 44px;
    display: grid;
    place-items: center;
    color: #606b67;
    font-size: 13px;
    font-weight: 900;
}

.st-key-mypage-shell [class*="st-key-mypage-generation-card-"] {
    --mypage-generation-content-width: 267px;
    height: 330px;
    overflow: hidden;
}

.st-key-mypage-shell
    [class*="st-key-mypage-generation-card-"]
    div[data-testid="stVerticalBlock"] {
    min-width: 0;
    max-width: 100%;
    overflow: hidden;
}

.st-key-mypage-shell
    [class*="st-key-mypage-generation-card-"]
    div[data-testid="stImage"] {
    height: 150px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    border-radius: 8px;
    background: #eef2ef;
}

.st-key-mypage-shell
    [class*="st-key-mypage-generation-card-"]
    div[data-testid="stImage"] img {
    width: 100%;
    height: 150px;
    object-fit: contain;
}

.st-key-mypage-shell
    [class*="st-key-mypage-generation-card-"]
    div[data-testid="stImage"],
.st-key-mypage-shell
    [class*="st-key-mypage-generation-card-"]
    .mypage-empty-thumb,
.st-key-mypage-shell
    [class*="st-key-mypage-generation-card-"]
    .mypage-generating-thumb,
.st-key-mypage-shell
    [class*="st-key-mypage-generation-card-"]
    .mypage-stale-thumb,
.st-key-mypage-shell
    [class*="st-key-mypage-generation-card-"]
    .mypage-card-meta,
.st-key-mypage-shell
    [class*="st-key-mypage-generation-card-"]
    div[data-testid="stSelectbox"],
.st-key-mypage-shell
    [class*="st-key-mypage-generation-card-"]
    div[data-testid="stHorizontalBlock"] {
    width: min(100%, var(--mypage-generation-content-width));
    max-width: 100%;
    margin-left: auto;
    margin-right: auto;
    box-sizing: border-box;
}

.mypage-card-meta {
    width: 100%;
    min-width: 0;
    max-width: 100%;
    box-sizing: border-box;
    display: grid;
    grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.35fr);
    align-items: center;
    gap: 8px;
    margin-top: 12px;
    overflow: hidden;
    color: #46524f;
    font-size: 13px;
    font-weight: 700;
}

.mypage-card-meta span {
    min-width: 0;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.mypage-card-meta span:last-child {
    justify-self: end;
    text-align: right;
}

.mypage-card-date {
    margin: 4px 0 10px;
    color: #7b8580;
    font-size: 13px;
}

.mypage-empty-state {
    min-height: 360px;
    display: grid;
    place-items: center;
    align-content: center;
    gap: 10px;
    border: 1px dashed #cad1cd;
    border-radius: 8px;
    background: #fbfcfa;
    text-align: center;
    color: #606b67;
}

.mypage-empty-state strong {
    color: #17201e;
    font-size: 22px;
}

.mypage-empty-state span {
    max-width: 420px;
    line-height: 1.6;
}
"""

MYPAGE_CARDS_CSS = "\n".join(
    (
        MYPAGE_CARD_LAYOUT_CSS.strip(),
        MYPAGE_CARD_THUMBNAILS_CSS.strip(),
        MYPAGE_CARD_ACTIONS_CSS.strip(),
    )
)
