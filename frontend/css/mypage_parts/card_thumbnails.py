MYPAGE_CARD_THUMBNAILS_CSS = """
.mypage-empty-thumb {
    height: var(--mypage-generation-thumb-height);
    display: grid;
    place-items: center;
    border-radius: 8px;
    background: #eef2ef;
    color: #7b8580;
    font-weight: 700;
}

.mypage-generating-thumb {
    height: var(--mypage-generation-thumb-height);
    display: grid;
    place-items: center;
    align-content: center;
    gap: 6px;
    border-radius: 8px;
    background: #eef7f4;
    color: #246257;
    text-align: center;
    box-sizing: border-box;
}

.mypage-generating-thumb strong {
    color: #173f39;
    font-size: 14px;
    font-weight: 900;
    line-height: 1.2;
}

.mypage-generating-thumb span {
    color: #5a756f;
    font-size: 12px;
    font-weight: 800;
    line-height: 1.25;
}

.mypage-generating-spinner {
    width: 34px;
    height: 34px;
    border-radius: 999px;
    border: 4px solid rgba(15, 143, 127, 0.16);
    border-top-color: #0f8f7f;
    border-right-color: #6fc5b9;
    animation: mypage-thumb-spin 0.85s linear infinite;
}

.mypage-stale-thumb {
    height: var(--mypage-generation-thumb-height);
    display: grid;
    place-items: center;
    align-content: center;
    gap: 7px;
    border-radius: 8px;
    background: #f4f1eb;
    color: #6d6257;
    text-align: center;
    box-sizing: border-box;
}

.mypage-stale-thumb strong {
    max-width: 180px;
    color: #3f3832;
    font-size: 14px;
    font-weight: 900;
    line-height: 1.25;
}

.mypage-stale-thumb span {
    color: #7f7367;
    font-size: 12px;
    font-weight: 800;
    line-height: 1.25;
}

@keyframes mypage-thumb-spin {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}
"""
