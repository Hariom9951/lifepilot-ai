# ==============================================================================
# LifePilot AI - Backend Dockerfile (Optimized & Secured)
# ==============================================================================

# Stage 1: Build virtual environment
FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=2.4.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main --no-root

# Stage 2: Production runner
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Create a non-root group and user
RUN groupadd --system --gid 10001 appgroup && \
    useradd --system --uid 10000 --gid appgroup --create-home --shell /bin/bash appuser

# Copy virtualenv and build outputs
COPY --from=builder /app/.venv /app/.venv

# Copy application source and change ownership
COPY --chown=appuser:appgroup app/ ./app/
COPY --chown=appuser:appgroup migrations/ ./migrations/
COPY --chown=appuser:appgroup alembic.ini ./

# Ensure storage directories exist and are owned by appuser
RUN mkdir -p storage/uploads storage/faiss storage/chroma logs && \
    chown -R appuser:appgroup storage logs

USER appuser

EXPOSE 8000

# Leverage python's urllib for a lightweight healthcheck to verify /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
