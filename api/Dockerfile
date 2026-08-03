# Step 29, API half. Multi-stage so the runtime image carries no build tooling.
#
# Build context is the repo root, because the API imports from ingest/ (the schema, the
# normalizer, the skill vocabulary) — those are one system, not two:
#
#   docker build -f api/Dockerfile -t hn-api .
#   docker run --rm -p 8000:8000 -v "$PWD/data:/data:ro" -e PARQUET_URI=/data/postings.parquet hn-api

FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Dependencies resolve from the lockfile before any source is copied, so editing a .py file
# doesn't invalidate the dependency layer.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY api/ ./api/
COPY ingest/ ./ingest/
COPY evals/ ./evals/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


FROM python:3.13-slim AS runtime

# Non-root. Nothing in the request path writes outside /tmp.
RUN useradd --create-home --uid 10001 app
WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/api /app/api
COPY --from=builder --chown=app:app /app/ingest /app/ingest
COPY --from=builder --chown=app:app /app/evals /app/evals

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PARQUET_CACHE=/tmp/postings.parquet

USER app
EXPOSE 8000

# Cloud Run sets $PORT, so it has to be expanded at runtime — hence shell form. `exec` keeps
# uvicorn as PID 1 so SIGTERM reaches it and the container stops cleanly.
#
# `python -m uvicorn`, not the `uvicorn` shim: console scripts bake an absolute interpreter
# path at install time, and a venv that moves between build stages leaves them pointing at a
# path that no longer exists. The module form uses whichever python is on PATH.
CMD exec python -m uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
