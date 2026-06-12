FROM python:3.11.14-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1
ENV PATH="/app/.venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:0.9.22 /uv /uvx /bin/

COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --frozen

COPY backend ./backend
COPY config ./config
# 컨테이너 시작 시 마이그레이션 자동 적용을 위해 Alembic 설정·파일 포함.
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations

EXPOSE 8000
# Render가 주입하는 PORT를 사용한다. 컨테이너 시작 시 alembic upgrade head를 먼저 돌리고
# uvicorn을 띄워 prod DB 스키마가 항상 최신이 되도록 보장한다.
CMD ["sh", "-c", "alembic upgrade head && uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
