FROM python:3.12-slim-bookworm AS base
FROM base AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY uv.lock pyproject.toml /app/
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-install-project --no-dev --native-tls --allow-insecure-host https://files.pythonhosted.org --allow-insecure-host https://pypi.org
COPY ./src README.md /app/
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev --allow-insecure-host https://files.pythonhosted.org  --allow-insecure-host https://pypi.org
FROM base
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"
ENV AOS_SSH_URL="http://localhost:8110"
ENV MCP_TRANSPORT="streamable-http"
EXPOSE 8110
WORKDIR /app
CMD python -m ale_aos_mcp --transport $MCP_TRANSPORT --aos-url $AOS_SSH_URL