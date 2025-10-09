# syntax=docker/dockerfile:1.7
FROM python:3.12-slim-bookworm AS base

FROM base AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY uv.lock pyproject.toml VERSION /app/
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-install-project --no-dev --native-tls --allow-insecure-host https://files.pythonhosted.org
COPY ./src README.md /app/
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --native-tls --frozen --no-dev --allow-insecure-host https://files.pythonhosted.org  --allow-insecure-host https://pypi.org

FROM base AS runtime
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app
EXPOSE 8110
CMD ["python", "-m", "ale_aos_ssh", "--port", "8110"]
