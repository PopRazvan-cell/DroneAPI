# syntax=docker/dockerfile:1.7

# Rasterio, pyproj, geopandas and shapely wheels bundle GDAL/PROJ/GEOS.
# We never compile GDAL in this image (see docs/dev-plan/01-repo-infra.md, Capcane).

ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.19 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project --group geo --group cv

COPY src ./src
RUN uv sync --frozen --no-dev --group geo --group cv --no-editable


FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PATH="/app/.venv/bin:${PATH}" \
    HOME=/tmp \
    USER=agridrone \
    LOGNAME=agridrone

RUN apt-get update \
    && apt-get install --yes --no-install-recommends libexpat1 libglib2.0-0 libgomp1 libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 agridrone \
    && useradd --uid 1000 --gid 1000 --create-home --shell /usr/sbin/nologin agridrone \
    && mkdir -p /data/store/_uploads /data/synthetic /data/public /data/samples /data/work \
    && chown -R agridrone:agridrone /data

WORKDIR /app

COPY --chown=agridrone:agridrone --from=builder /app/.venv /app/.venv
COPY --chown=agridrone:agridrone --from=builder /app/src /app/src
COPY --chown=agridrone:agridrone pyproject.toml README.md ./

USER agridrone

EXPOSE 8000

CMD ["uvicorn", "agridrone.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
