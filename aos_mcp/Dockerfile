# syntax=docker/dockerfile:1.7
FROM python:3.12-slim-bookworm AS base

FROM base AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY uv.lock pyproject.toml VERSION /app/
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-install-project --no-dev --native-tls --allow-insecure-host https://files.pythonhosted.org --allow-insecure-host https://pypi.org
COPY ./src README.md /app/
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev --allow-insecure-host https://files.pythonhosted.org  --allow-insecure-host https://pypi.org

FROM base AS runtime
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"
ENV ALE_AOS_MCP_SSH_URL="http://localhost:8110"
ENV ALE_AOS_MCP_TRANSPORT="streamable-http"
ENV ALE_AOS_MCP_PORT="8000"
ENV ALE_AOS_MCP_TOOLS_FILE=""
ENV ALE_AOS_MCP_LOG_LEVEL="INFO"
EXPOSE 8000
WORKDIR /app
CMD ["python", "-m","ale_aos_mcp"]
