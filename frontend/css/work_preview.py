WORK_PREVIEW_CSS = """
:root {
    --work-preview-height: 620px;
    --work-generate-button-height: 60px;
}

.preview-shell {
    display: flex;
    flex-direction: column;
    height: var(--work-preview-height, 620px);
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
    flex: 1 1 auto;
    min-height: 0;
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
    flex: 1 1 auto;
    min-height: 0;
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
    flex: 1 1 auto;
    min-height: 0;
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

.st-key-preview-history-controls {
    width: 100%;
    margin: 0;
}

.preview-history-controls { display: none; }

.result-summary-panel {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 14px;
}

.preview-shell > .result-summary-panel { margin: 0 0 12px; }

.result-summary-chip {
    display: inline-flex;
    align-items: center;
    min-height: 32px;
    padding: 6px 11px;
    border: 1px solid rgba(32, 39, 37, 0.12);
    border-radius: 8px;
    color: #202725;
    font-size: 13px;
    font-weight: 900;
    line-height: 1.35;
    box-sizing: border-box;
    overflow-wrap: anywhere;
}

.result-summary-chip.is-included {
    background: #eaf7f0;
    border-color: rgba(35, 119, 80, 0.22);
    color: #206245;
}

.result-summary-chip.is-excluded {
    background: #f3f0ea;
    border-color: rgba(93, 103, 100, 0.18);
    color: #69736f;
}

.result-copy-panel {
    width: 100%;
    margin: 0;
    margin-top: -16px;
    border: 1px solid rgba(32, 39, 37, 0.12);
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.95);
    padding: 12px 14px;
    color: #202725;
    box-sizing: border-box;
    overflow-wrap: anywhere;
}

.result-copy-mode {
    display: inline-flex;
    margin: 0 0 8px;
    color: #5d6764;
    font-size: 12px;
    font-weight: 900;
}

.result-copy-line {
    display: grid;
    grid-template-columns: 70px minmax(0, 1fr);
    gap: 12px;
    align-items: start;
    margin: 7px 0 0;
    line-height: 1.5;
}

.result-copy-line span {
    color: #7a8581;
    font-size: 12px;
    font-weight: 900;
}

.result-copy-line strong {
    min-width: 0;
    color: #202725;
    font-size: 14px;
    font-weight: 800;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
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
