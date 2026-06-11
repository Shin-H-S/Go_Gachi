BASE_CSS = """
:root {
    --paper: #f8f7f2;
    --panel: #fffdf8;
    --ink: #202725;
    --muted: #66716d;
    --line: #dfded6;
    --teal: #0f8f7f;
    --teal-dark: #087163;
}

html,
body,
.stApp,
[data-testid="stAppViewContainer"] {
    color-scheme: light;
}

.stApp {
    background: linear-gradient(180deg, #f4f1e9 0%, #fbfaf4 48%, #f1f7f5 100%);
    color: var(--ink);
}

.main .block-container {
    max-width: 1360px;
    padding: 24px 28px 40px;
}

[data-testid="stHeader"] {
    background: transparent;
}

h1, h2, h3, p {
    letter-spacing: 0;
}

div[data-testid="stAlert"],
div[data-testid="stAlert"] *,
div[data-testid="stAlert"] p {
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}
"""
