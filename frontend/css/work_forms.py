WORK_FORMS_CSS = """
.section-label,
p.section-label {
    color: #3a4240;
    font-size: 20px !important;
    font-weight: 900;
    margin: 0 0 8px;
}

.small-note {
    color: var(--muted);
    font-size: 13px;
    line-height: 1.55;
    margin: 0 0 12px;
}

.format-readout {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    border: 1px solid rgba(32, 39, 37, 0.12);
    border-radius: 8px;
    background: #f5f4ee;
    padding: 12px 14px;
    margin: 6px 0 14px;
    color: #29312f;
    font-size: 13px;
    font-weight: 800;
}

.format-readout .channel-name {
    color: var(--ink);
    font-size: 17px;
    font-weight: 950;
    line-height: 1.2;
}

.format-readout .format-size {
    color: var(--ink);
    font-size: 18px;
    font-weight: 950;
    line-height: 1;
    white-space: nowrap;
}

.format-readout strong,
.format-readout small {
    display: block;
}

.format-readout small {
    color: var(--muted);
    font-size: 12px;
    font-weight: 700;
    margin-top: 4px;
}

.detail-choice-label,
p.detail-choice-label {
    color: #3a4240;
    font-size: 20px !important;
    font-weight: 900;
    margin: 0 0 8px;
}

.st-key-left-options-panel {
    height: var(--work-preview-height, 620px);
    max-height: var(--work-preview-height, 620px);
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 1px solid rgba(32, 39, 37, 0.14) !important;
    border-radius: 8px !important;
    box-shadow: 0 10px 22px rgba(44, 47, 42, 0.055);
    box-sizing: border-box;
    scrollbar-gutter: stable;
}

.st-key-left-options-panel::-webkit-scrollbar {
    width: 10px;
}

.st-key-left-options-panel::-webkit-scrollbar-track {
    background: #f0eee7;
    border-radius: 999px;
}

.st-key-left-options-panel::-webkit-scrollbar-thumb {
    background: rgba(15, 143, 127, 0.45);
    border: 2px solid #f0eee7;
    border-radius: 999px;
}

.st-key-left-options-panel::-webkit-scrollbar-thumb:hover {
    background: rgba(15, 143, 127, 0.64);
}

.st-key-left-options-panel > div,
.st-key-left-options-panel [data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 0 !important;
    box-shadow: none !important;
}

.st-key-left-upload-section,
.st-key-left-channel-section,
.st-key-left-type-section {
    padding-bottom: 20px;
    margin-bottom: 20px;
    border-bottom: 1px solid rgba(32, 39, 37, 0.1) !important;
}

.st-key-left-prompt-section {
    padding-bottom: 4px;
}

.left-options-scroll-marker {
    display: none;
}

"""
