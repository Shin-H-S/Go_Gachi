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
# Alembic 설정과 마이그레이션 스크립트도 함께 복사해 컨테이너 안에서 `alembic upgrade head`가 가능하게 한다.
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations

EXPOSE 8080
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
