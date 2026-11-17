# Production image: one container serves the API and the built React app.
#
# Multi-stage build: stage 1 has Node and builds the frontend; stage 2 is a slim Python
# image that copies in only the built files. Node never ships to production.

# ---------- stage 1: build the frontend ----------
FROM node:22-alpine AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---------- stage 2: the runtime ----------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ENVIRONMENT=production \
    STATIC_DIR=/app/static \
    PORT=8000

WORKDIR /app

# Dependencies first: this layer is cached until pyproject.toml changes.
COPY backend/pyproject.toml ./
RUN pip install .

COPY backend/ ./
COPY --from=frontend /build/dist ./static

# Never run as root inside the container.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# On every start: apply pending migrations, then serve.
# --proxy-headers: the host's load balancer terminates HTTPS and forwards the request.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
