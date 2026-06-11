# Repository Agent Instructions

## Personal Manual Site Launch Requests

The detailed private runbook is `docs/local-manual-testing.md`. Read and follow it before
handling either request below.

Although the Korean trigger phrases say "창을 띄워주세요", never open, navigate, show, or
control a browser window. Interpret them as requests to configure the requested mode, start
the required local server processes, confirm the frontend URL responds, and return only the
clickable frontend URL. The user will open the browser themselves.

When the user says:

> 제가 프론트엔드만 확인할수 있게 창을 띄워주세요

start only the Streamlit frontend in explicit frontend mock mode. Do not start the backend
and do not open the in-app browser. Return the clickable URL `http://127.0.0.1:8501`.

When the user says:

> 프론트+백엔드를 확인할수 있게 창을 띄워주세요

start the real backend on fixed port `8077`, connect the frontend to
`http://127.0.0.1:8077`, enable the real OpenAI provider, start the frontend on port `8501`,
and return the clickable URL `http://127.0.0.1:8501`. Do not open the in-app browser.

For both requests:

- These are manual browser inspection requests, not requests to run automated tests.
- Never open or control a browser window. The user opens the returned URL themselves.
- Preserve existing `.env` values and secrets, changing only the required mode variables.
- Never expose secrets.
- Do not silently replace missing real backend/OpenAI settings with mock settings.
- Do not silently use a backend port other than `8077`.
- Start background server processes with hidden windows.
- Keep launch work minimal: configure the requested mode, start the required server processes,
  confirm the frontend URL responds, and return the URL.
