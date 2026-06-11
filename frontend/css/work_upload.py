WORK_UPLOAD_CSS = """
div[data-testid="stFileUploader"] section {
    border: 1px dashed rgba(15, 143, 127, 0.42);
    border-radius: 8px;
    background: #f5f4ee !important;
    color: var(--ink) !important;
}

div[data-testid="stFileUploaderFile"],
div[data-testid="stFileUploaderFile"] > div,
div[data-testid="stFileUploaderDropzone"] {
    background: #f5f4ee !important;
    background-color: #f5f4ee !important;
    color: var(--ink) !important;
}

div[data-testid="stFileUploaderFile"],
div[data-testid="stFileUploaderFile"] > div,
div[data-testid="stFileUploaderFile"] [data-testid="stFileUploaderFileName"],
div[data-testid="stFileUploaderFile"] [data-testid="stFileUploaderFileSize"] {
    background: #ffffff !important;
    background-color: #ffffff !important;
    color: #202725 !important;
    -webkit-text-fill-color: #202725 !important;
}

div[data-testid="stFileUploader"] section *,
div[data-testid="stFileUploaderFile"] *,
div[data-testid="stFileUploaderDropzone"] * {
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
}

div[data-testid="stFileUploaderFile"] button,
div[data-testid="stFileUploaderFile"] button * {
    background: #ffffff !important;
    background-color: #ffffff !important;
    color: #202725 !important;
    -webkit-text-fill-color: #202725 !important;
}

div[data-testid="stFileUploader"] button {
    background: #ffffff !important;
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
    border: 1px solid rgba(32, 39, 37, 0.14) !important;
}

.st-key-logo_upload:has([data-testid="stFileUploaderFile"])
    section > div:not(:has([data-testid="stFileUploaderFile"])) button,
.st-key-logo_upload:has([data-testid="stFileUploaderFile"])
    [data-testid="stFileUploaderDropzone"] button {
    display: none !important;
}

.st-key-logo_upload:has([data-testid="stFileUploaderFile"])
    section > div:has([data-testid="stFileUploaderFile"]) button,
.st-key-logo_upload:has([data-testid="stFileUploaderFile"])
    [data-testid="stFileUploaderFile"] button {
    display: inline-flex !important;
}

.st-key-left-logo-section,
.st-key-left-logo-preview-section {
    height: 264px;
    min-height: 264px;
}

.st-key-left-logo-preview-section {
    padding-bottom: 16px !important;
}

.logo-preview-frame {
    width: 100%;
    height: 232px;
    min-height: 232px;
    box-sizing: border-box;
    border: 1px dashed rgba(15, 143, 127, 0.42);
    border-radius: 8px;
    background: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    padding: 8px;
}

.logo-preview-frame img {
    display: block;
    max-width: 100%;
    max-height: 100%;
    width: auto;
    height: auto;
    object-fit: contain;
}

.logo-preview-placeholder {
    color: #7a8581;
    -webkit-text-fill-color: #7a8581;
    font-size: 18px;
    font-weight: 700;
}

div[role="radiogroup"] {
    gap: 6px;
}
"""
