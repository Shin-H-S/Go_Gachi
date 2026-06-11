MAIN_VISUAL_CSS = """
.hero-visual {
    --slide-height: min(62vh, 620px);
    width: 100%;
    padding-top: 74px;
}

.blue-slide-window {
    position: relative;
    height: var(--slide-height);
    min-height: 520px;
    border-radius: 42px;
    overflow: hidden;
    background: #0d5bff;
    box-shadow: 0 28px 58px rgba(12, 34, 86, 0.26);
}

.blue-slide-track {
    animation: blue-panel-slide 12s linear infinite;
}

.blue-panel {
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    height: var(--slide-height);
    min-height: 520px;
    padding: 44px;
    background:
        linear-gradient(180deg, rgba(255,255,255,0.18) 0%, rgba(255,255,255,0) 28%),
        #075cff;
    color: #ffffff;
    box-sizing: border-box;
}

.blue-panel-two {
    background:
        linear-gradient(180deg, rgba(255,255,255,0.20) 0%, rgba(255,255,255,0) 30%),
        #006df2;
}

.blue-panel-three {
    background:
        linear-gradient(180deg, rgba(255,255,255,0.22) 0%, rgba(255,255,255,0) 32%),
        #1557d8;
}

.blue-panel span {
    color: rgba(255, 255, 255, 0.82);
    font-size: 18px;
    font-weight: 900;
    margin-bottom: 10px;
}

.blue-panel strong {
    color: #ffffff;
    font-size: 56px;
    line-height: 1.02;
    font-weight: 950;
}

@keyframes blue-panel-slide {
    0%, 18% {
        transform: translateY(0);
    }
    28%, 46% {
        transform: translateY(calc(var(--slide-height) * -1));
    }
    56%, 74% {
        transform: translateY(calc(var(--slide-height) * -2));
    }
    84%, 100% {
        transform: translateY(calc(var(--slide-height) * -3));
    }
}
"""
