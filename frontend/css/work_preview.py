WORK_PREVIEW_CSS = """
.preview-shell {
    height: 620px;
    border: 1px solid rgba(32, 39, 37, 0.13);
    border-radius: 8px;
    background:
        linear-gradient(45deg, rgba(32,39,37,0.035) 25%, transparent 25%),
        linear-gradient(-45deg, rgba(32,39,37,0.035) 25%, transparent 25%),
        linear-gradient(45deg, transparent 75%, rgba(32,39,37,0.035) 75%),
        linear-gradient(-45deg, transparent 75%, rgba(32,39,37,0.035) 75%),
        #fbfaf4;
    background-size: 28px 28px;
    background-position: 0 0, 0 14px, 14px -14px, -14px 0;
    padding: 18px;
    box-sizing: border-box;
    overflow: hidden;
}

.result-caption {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    color: #5d6764;
    font-size: 13px;
    font-weight: 800;
    margin: 0 0 10px;
}

.empty-guide {
    display: flex;
    height: calc(100% - 28px);
    align-items: center;
    justify-content: center;
    text-align: center;
    color: #5d6764;
    font-size: 18px;
    font-weight: 900;
    line-height: 1.65;
}

.loading-state {
    display: flex;
    height: calc(100% - 28px);
    align-items: flex-start;
    justify-content: center;
    padding-top: 150px;
    box-sizing: border-box;
    text-align: center;
}

.loading-panel {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
    color: #4d5960;
    font-size: 18px;
    font-weight: 900;
    line-height: 1.55;
}

.loading-spinner {
    width: 54px;
    height: 54px;
    border-radius: 999px;
    border: 6px solid rgba(108, 94, 214, 0.14);
    border-top-color: #5145c6;
    border-right-color: #a790ff;
    animation: spin 0.85s linear infinite;
}

.preview-image-frame {
    height: calc(100% - 28px);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

.preview-image-frame img {
    display: block;
    max-width: 100%;
    max-height: 100%;
    width: auto;
    height: auto;
    object-fit: contain;
    border-radius: 8px;
    border: 1px solid rgba(32, 39, 37, 0.12);
    box-sizing: border-box;
}

@keyframes spin {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}
"""
