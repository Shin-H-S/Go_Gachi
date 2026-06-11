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
# Railway preDeployCommand에서 `alembic upgrade head`를 실행할 수 있도록
# Alembic 설정과 마이그레이션 파일을 이미지에 포함한다.
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations

EXPOSE 8000
# Railway가 주입하는 PORT를 사용한다. railway.toml의 startCommand가 우선 적용되며,
# 이 CMD는 Dockerfile 단독 실행 시의 기본 실행 명령이다.
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
