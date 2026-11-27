FROM python:3.13-slim AS build

COPY --from=ghcr.io/astral-sh/uv:0.11.16 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_NO_DEV=1 UV_PYTHON_DOWNLOADS=0

WORKDIR /repo/server
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=server/uv.lock,target=uv.lock \
    --mount=type=bind,source=server/pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project
COPY server/ ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked


FROM python:3.13-slim

RUN useradd --create-home --uid 10001 app
WORKDIR /repo/server
COPY --from=build --chown=app:app /repo/server ./
COPY --chown=app:app assessment/seed.json /repo/assessment/seed.json
ENV PATH=/repo/server/.venv/bin:$PATH PYTHONUNBUFFERED=1
USER app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
