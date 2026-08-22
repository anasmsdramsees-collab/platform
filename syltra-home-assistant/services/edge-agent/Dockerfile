# SYLTRA Edge Agent — built from the repo root as build context:
#   docker build -f services/edge-agent/Dockerfile .
# No secrets are baked into this image (spec §25.3); configuration and the
# Home Assistant token arrive via environment at runtime.

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY libs ./libs
COPY simulator ./simulator
COPY services/edge-agent ./services/edge-agent
RUN uv sync --frozen --no-dev --package syltra-edge-agent

FROM python:3.12-slim-bookworm
RUN useradd --create-home --uid 1000 syltra
WORKDIR /app
COPY --from=build --chown=syltra:syltra /app /app
USER syltra
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8081
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8081/health/live', timeout=4)"
CMD ["syltra-edge-agent"]
