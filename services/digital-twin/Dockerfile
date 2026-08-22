# SYLTRA Digital Twin — built from the repo root as build context:
#   docker build -f services/digital-twin/Dockerfile .
# No secrets are baked in (spec §25.3); configuration arrives via environment.

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY libs ./libs
COPY simulator ./simulator
COPY services ./services
RUN uv sync --frozen --no-dev --package syltra-digital-twin

FROM python:3.12-slim-bookworm
RUN useradd --create-home --uid 1000 syltra
WORKDIR /app
COPY --from=build --chown=syltra:syltra /app /app
COPY --chown=syltra:syltra alembic.ini ./
COPY --chown=syltra:syltra infrastructure/migrations ./infrastructure/migrations
USER syltra
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8082
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8082/health/live', timeout=4)"
CMD ["syltra-digital-twin"]
