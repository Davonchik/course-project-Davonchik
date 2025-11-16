# syntax=docker/dockerfile:1.7
# === build ===
FROM python:3.12-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc \
      libpq-dev \
  && rm -rf /var/lib/apt/lists/* && apt-get clean
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

# === runtime ===
FROM python:3.12-slim AS runtime
LABEL org.opencontainers.image.title="Reading List API" \
      org.opencontainers.image.description="Secure reading list service with RBAC" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="HSE SEC Course Project" \
      maintainer="dgaslanian"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app
# runtime зависимости только
RUN apt-get update && apt-get install -y --no-install-recommends \
      libpq5 \
      curl \
      ca-certificates \
  && rm -rf /var/lib/apt/lists/* && apt-get clean

# non-root
RUN groupadd -r -g 1000 appuser && \
    useradd  -r -u 1000 -g appuser -m -d /home/appuser -s /sbin/nologin appuser

# deps из wheels
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache \
    pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt && \
    rm -rf /wheels

# код приложения
COPY --chown=appuser:appuser . .

EXPOSE 8000
USER appuser
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/health || exit 1
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","1"]
