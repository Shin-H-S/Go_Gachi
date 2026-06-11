MYPAGE_CARDS_CSS = """
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

.mypage-empty-thumb {
    height: 150px;
    display: grid;
    place-items: center;
    border-radius: 8px;
    background: #eef2ef;
    color: #7b8580;
    font-weight: 700;
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

.st-key-mypage-shell [class*="st-key-mypage-original-"] a,
.st-key-mypage-shell [class*="st-key-mypage-original-"] button,
.st-key-mypage-shell [class*="st-key-mypage-original-"] div[data-testid="stLinkButton"] a,
.st-key-mypage-shell [class*="st-key-mypage-original-"] div[data-testid="stButton"] button,
.st-key-mypage-shell [class*="st-key-mypage-download-"] button,
.st-key-mypage-shell [class*="st-key-mypage-download-"] div[data-testid="stDownloadButton"] button {
    height: 34px !important;
    min-height: 34px !important;
    padding: 0 10px !important;
    box-sizing: border-box !important;
    display: flex !important;
    align-items: center;
    justify-content: center;
    border-width: 1px !important;
    border-style: solid !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    font-size: 13px !important;
    font-weight: 900 !important;
    line-height: 1 !important;
}

.st-key-mypage-shell [class*="st-key-mypage-original-"] a,
.st-key-mypage-shell [class*="st-key-mypage-original-"] button {
    background: #f5f4ee !important;
    border-color: #d7d2c7 !important;
    color: #46524f !important;
    -webkit-text-fill-color: #46524f !important;
}

.st-key-mypage-shell [class*="st-key-mypage-download-"] button,
.st-key-mypage-shell [class*="st-key-mypage-download-"] div[data-testid="stDownloadButton"] button {
    background: #eaf4ff !important;
    border-color: #b9d6f5 !important;
    color: #245c8f !important;
    -webkit-text-fill-color: #245c8f !important;
}

.st-key-mypage-shell [class*="st-key-mypage-download-"] button:disabled {
    background: #f4f8fc !important;
    border-color: #d7e2ea !important;
    color: #8a98a4 !important;
    -webkit-text-fill-color: #8a98a4 !important;
    opacity: 0.65;
}

.st-key-mypage-shell [class*="st-key-mypage-original-"] a p,
.st-key-mypage-shell [class*="st-key-mypage-original-"] button p,
.st-key-mypage-shell [class*="st-key-mypage-download-"] button p {
    margin: 0;
    line-height: 1 !important;
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
