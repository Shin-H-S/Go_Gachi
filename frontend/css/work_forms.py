WORK_FORMS_CSS = """
.topbar {
    padding-bottom: 18px;
    border-bottom: 1px solid rgba(32, 39, 37, 0.12);
    margin-bottom: 20px;
}

.brand-kicker {
    color: var(--teal-dark);
    font-size: 13px;
    font-weight: 900;
    margin: 0 0 8px;
}

.title {
    color: var(--ink);
    font-size: clamp(36px, 5vw, 62px);
    line-height: 1.02;
    font-weight: 950;
    margin: 0;
}

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

.st-key-left-upload-section,
.st-key-left-channel-section,
.st-key-left-type-section,
.st-key-left-prompt-section {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 1px solid rgba(32, 39, 37, 0.14) !important;
    border-radius: 8px !important;
    box-shadow: 0 10px 22px rgba(44, 47, 42, 0.055);
}

.st-key-left-upload-section > div,
.st-key-left-channel-section > div,
.st-key-left-type-section > div,
.st-key-left-prompt-section > div,
.st-key-left-upload-section [data-testid="stVerticalBlockBorderWrapper"],
.st-key-left-channel-section [data-testid="stVerticalBlockBorderWrapper"],
.st-key-left-type-section [data-testid="stVerticalBlockBorderWrapper"],
.st-key-left-prompt-section [data-testid="stVerticalBlockBorderWrapper"],
.st-key-left-upload-section [data-testid="stVerticalBlock"],
.st-key-left-channel-section [data-testid="stVerticalBlock"],
.st-key-left-type-section [data-testid="stVerticalBlock"],
.st-key-left-prompt-section [data-testid="stVerticalBlock"] {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 0 !important;
    box-shadow: none !important;
}
"""
