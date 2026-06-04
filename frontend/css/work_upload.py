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
    color: var(--ink) !important;
}

div[data-testid="stFileUploader"] section *,
div[data-testid="stFileUploaderFile"] *,
div[data-testid="stFileUploaderDropzone"] * {
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
}

div[data-testid="stFileUploader"] button {
    background: #ffffff !important;
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
    border: 1px solid rgba(32, 39, 37, 0.14) !important;
}

div[role="radiogroup"] {
    gap: 6px;
}
"""
