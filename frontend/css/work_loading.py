CAFE24_DONGDONG_FONT_URL = (
    "https://cdn.jsdelivr.net/gh/projectnoonnu/"
    "noonfonts_twelve@1.1/Cafe24Dongdong.woff"
)


WORK_LOADING_CSS = """
@font-face {
    font-family: Cafe24Dongdong;
    src: url("__CAFE24_DONGDONG_FONT_URL__") format("woff");
    font-weight: normal;
    font-style: normal;
    font-display: swap;
}

.loading-state {
    display: flex;
    flex: 1 1 auto;
    min-height: 0;
    align-items: stretch;
    justify-content: center;
    box-sizing: border-box;
    text-align: center;
}

.preview-shell .loading-tip-stage {
    --loading-tip-cycle: 119s;
    --loading-tip-step: 7s;
    position: relative;
    flex: 1 1 auto;
    width: 100%;
    min-height: 0;
    overflow: hidden;
    border-radius: 8px;
    color: #5A514B;
    background: #9fdcf5;
    pointer-events: none;
}

.loading-tip-card {
    position: absolute;
    inset: 0;
    display: grid;
    grid-template-rows: minmax(0, 1fr) auto 25%;
    justify-items: center;
    padding: 0 52px;
    box-sizing: border-box;
    color: #5A514B;
    background: var(--tip-bg);
    opacity: 0;
    transform: translateY(6px);
    animation: loading-tip-card-cycle var(--loading-tip-cycle) linear infinite;
    animation-delay: calc(var(--tip-index) * var(--loading-tip-step));
}

.loading-tip-content {
    position: relative;
    z-index: 1;
    display: flex;
    grid-row: 2;
    width: min(100%, 520px);
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.loading-clay-icon-wrap {
    display: flex;
    width: 100%;
    justify-content: center;
    margin: 0 auto 18px;
}

.loading-clay-icon {
    display: block;
    width: clamp(132px, 32%, 178px);
    aspect-ratio: 1;
    height: auto;
    object-fit: contain;
}

.loading-tip-heading {
    display: flex;
    width: 100%;
    align-items: center;
    justify-content: center;
}

.loading-tip-content strong {
    max-width: 100%;
    color: #5A514B;
    font-family: Cafe24Dongdong, "Malgun Gothic", sans-serif;
    font-size: 21px;
    font-weight: 700;
    line-height: 1.52;
    letter-spacing: 0;
    text-align: center;
    text-shadow: 0 -1px 0 rgba(255, 255, 255, 0.18);
    overflow-wrap: anywhere;
}

.loading-tip-content p {
    max-width: 100%;
    margin: 12px 0 0;
    color: #5A514B;
    font-family: Cafe24Dongdong, "Malgun Gothic", sans-serif;
    font-size: 21px;
    font-weight: 700;
    line-height: 1.52;
    letter-spacing: 0;
    text-align: center;
    text-shadow: 0 -1px 0 rgba(255, 255, 255, 0.18);
    overflow-wrap: anywhere;
}

.loading-status {
    position: absolute;
    z-index: 2;
    left: 0;
    right: 0;
    bottom: 34px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 11px;
    color: #5e6864;
    font-size: 14px;
    font-weight: 900;
    line-height: 1;
}

.loading-progress-dots {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
}

.loading-progress-dots span {
    width: 7px;
    height: 7px;
    border-radius: 999px;
    background: #5e6864;
    opacity: 0.34;
    animation: loading-dot-pulse 1.25s ease-in-out infinite;
}

.loading-progress-dots span:nth-child(2) {
    animation-delay: 0.16s;
}

.loading-progress-dots span:nth-child(3) {
    animation-delay: 0.32s;
}

@keyframes loading-tip-card-cycle {
    0%,
    5.1% {
        opacity: 1;
        transform: translateY(0);
    }
    5.88%,
    100% {
        opacity: 0;
        transform: translateY(6px);
    }
}

@keyframes loading-dot-pulse {
    0%,
    80%,
    100% {
        opacity: 0.28;
        transform: translateY(0);
    }
    40% {
        opacity: 0.82;
        transform: translateY(-3px);
    }
}
""".replace("__CAFE24_DONGDONG_FONT_URL__", CAFE24_DONGDONG_FONT_URL)
