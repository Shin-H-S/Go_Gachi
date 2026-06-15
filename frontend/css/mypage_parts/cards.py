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
    --mypage-generation-thumb-height: 205px;
    height: 330px;
    overflow: hidden;
}

.st-key-mypage-shell [class*="st-key-mypage-generation-card-selected-"] {
    border-width: 3px !important;
    border-color: #00a6a6 !important;
    box-shadow: 0 0 0 1px rgba(0, 166, 166, 0.16) !important;
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
    height: var(--mypage-generation-thumb-height);
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
    height: var(--mypage-generation-thumb-height);
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
    .mypage-card-select-zone,
.st-key-mypage-shell
    [class*="st-key-mypage-generation-card-"]
    [class*="st-key-mypage-select-"] {
    width: min(100%, var(--mypage-generation-content-width));
    max-width: 100%;
    margin-left: auto;
    margin-right: auto;
    box-sizing: border-box;
}

.st-key-mypage-shell [class*="st-key-mypage-select-"] button {
    height: 32px !important;
    min-height: 32px !important;
    border-radius: 8px !important;
    border: 1px solid rgba(0, 166, 166, 0.32) !important;
    background: #f7fffd !important;
    color: #087a7a !important;
    -webkit-text-fill-color: #087a7a !important;
    font-size: 13px !important;
    font-weight: 900 !important;
    box-shadow: none !important;
}

.mypage-card-meta {
    width: 100%;
    min-width: 0;
    max-width: 100%;
    box-sizing: border-box;
    display: grid;
    grid-template-columns: minmax(0, 1.12fr) minmax(0, 0.88fr);
    align-items: center;
    gap: 10px;
    margin-top: 6px;
    margin-bottom: 2px;
    overflow: hidden;
    color: #46524f;
    font-size: 12px;
    font-weight: 700;
    line-height: 1.15;
}

.mypage-card-meta span {
    min-width: 0;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.mypage-card-identity {
    justify-self: start;
    text-align: left;
}

.mypage-card-folder {
    justify-self: end;
    text-align: right;
}

.mypage-card-select-zone {
    height: 0;
    margin: 0;
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
