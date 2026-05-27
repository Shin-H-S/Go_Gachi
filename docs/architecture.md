# Architecture

## Runtime Flow

1. The browser loads `frontend/index.html` and static assets from FastAPI.
2. The user uploads a cafe menu photo.
3. The browser normalizes the image to PNG with canvas to reduce API format errors.
4. The frontend sends the image data URL, preset id, and optional feedback to `/api/generate`.
5. FastAPI reads the API key from server-side environment variables only.
6. The image provider returns a generated image, and the browser exports it to the selected platform size.

## Cloud Runtime

Cloud Run runs the same FastAPI app from the Docker image built by `infra/Dockerfile`. The container listens on the `PORT` environment variable provided by Cloud Run. Secrets are injected at runtime through Secret Manager, not copied into the image.

## Folder Layout

- `backend/app`: FastAPI application code
- `config`: product presets and editable non-secret configuration
- `frontend`: static HTML, CSS, and browser JavaScript
- `infra`: Docker runtime assets
- `docs`: project documentation
- `tests`: automated tests
- `.github`: pull request and CI configuration
- `.vscode`: shared VSCode recommendations
- `cloudbuild.yaml`: Cloud Build pipeline for Cloud Run

## Secret Handling

Never place real API keys in source files. Local development uses `.env`, which is ignored by git and Docker build context. Cloud Run should use Secret Manager and inject `OPENAI_API_KEY` as an environment variable at runtime.
