# SYLTRA Adaptive Engine — built from the repo root as build context:
#   docker build -f services/adaptive-engine/Dockerfile .
# No secrets are baked in (spec §25.3); configuration arrives via environment.
# Models are trained per household on local data and never leave the hub.

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY libs ./libs
COPY simulator ./simulator
COPY services ./services
RUN uv sync --frozen --no-dev --package syltra-adaptive-engine

FROM python:3.12-slim-bookworm
RUN useradd --create-home --uid 1000 syltra
WORKDIR /app
COPY --from=build --chown=syltra:syltra /app /app
# Local model artifacts live here; the volume is hub-local and never synced.
RUN mkdir -p /app/models/exported && chown -R syltra:syltra /app/models
USER syltra
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8084
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8084/health/live', timeout=4)"
CMD ["syltra-adaptive-engine"]
