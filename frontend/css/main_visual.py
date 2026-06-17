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
    animation: blue-panel-slide 20s linear infinite;
}

.blue-panel {
    position: relative;
    isolation: isolate;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    height: var(--slide-height);
    min-height: 520px;
    padding: 44px;
    overflow: hidden;
    background:
        linear-gradient(180deg, rgba(255,255,255,0.18) 0%, rgba(255,255,255,0) 28%),
        #075cff;
    color: #ffffff;
    box-sizing: border-box;
}

.blue-panel::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(circle at 22% 18%, rgba(255, 255, 255, 0.30), transparent 32%),
        linear-gradient(180deg, rgba(1, 14, 45, 0) 46%, rgba(1, 14, 45, 0.54) 100%);
    pointer-events: none;
    z-index: 0;
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

.blue-panel-four {
    background:
        linear-gradient(180deg, rgba(255,255,255,0.18) 0%, rgba(255,255,255,0) 30%),
        #0a49c7;
}

.blue-panel-five {
    background:
        linear-gradient(180deg, rgba(255,255,255,0.20) 0%, rgba(255,255,255,0) 30%),
        #0877e8;
}

.blue-panel-image-stage {
    position: absolute;
    inset: 30px 30px 128px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 30px;
    transform: none;
    z-index: 2;
}

.blue-panel-image-stage::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    box-sizing: border-box;
    background: #ffffff;
    border: 1px solid rgba(18, 47, 91, 0.14);
    box-shadow:
        inset 1px 1px 0 rgba(255, 255, 255, 0.96),
        inset -1px -1px 0 rgba(18, 47, 91, 0.07),
        inset 0 0 18px rgba(18, 47, 91, 0.04),
        0 24px 38px rgba(0, 27, 90, 0.22);
    transform: rotate(-0.7deg);
    z-index: 0;
}

.blue-panel-image {
    position: relative;
    display: block;
    width: min(86%, 620px);
    height: min(86%, 620px);
    object-fit: contain;
    border-radius: 22px;
    transform: none;
    filter: drop-shadow(0 16px 20px rgba(2, 18, 56, 0.18));
    z-index: 1;
}

.blue-panel-caption {
    position: relative;
    z-index: 3;
}

.blue-panel-caption span {
    color: rgba(255, 255, 255, 0.82);
    font-size: 18px;
    font-weight: 900;
    margin-bottom: 10px;
}

.blue-panel-caption strong {
    display: block;
    color: #ffffff;
    font-size: 42px;
    line-height: 1.02;
    font-weight: 950;
}

@keyframes blue-panel-slide {
    0%, 12% {
        transform: translateY(0);
    }
    18%, 30% {
        transform: translateY(calc(var(--slide-height) * -1));
    }
    36%, 48% {
        transform: translateY(calc(var(--slide-height) * -2));
    }
    54%, 66% {
        transform: translateY(calc(var(--slide-height) * -3));
    }
    72%, 84% {
        transform: translateY(calc(var(--slide-height) * -4));
    }
    90%, 100% {
        transform: translateY(calc(var(--slide-height) * -5));
    }
}
"""
