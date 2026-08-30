FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
RUN uv pip install --system --no-cache .

COPY sella_core sella_core
COPY providers providers
COPY integrations integrations
COPY policies policies
COPY tools tools
COPY audit audit
COPY apps apps
COPY observability observability

EXPOSE 8090
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8090"]
