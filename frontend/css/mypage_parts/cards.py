MYPAGE_CARDS_CSS = """
.mypage-card-grid,
.mypage-card-grid-marker {
    margin-top: 8px;
}

.mypage-empty-thumb {
    aspect-ratio: 4 / 3;
    display: grid;
    place-items: center;
    border-radius: 8px;
    background: #eef2ef;
    color: #7b8580;
    font-weight: 700;
}

.mypage-card-meta {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    margin-top: 12px;
    color: #46524f;
    font-size: 13px;
    font-weight: 700;
}

.mypage-card-meta span {
    max-width: 50%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
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
