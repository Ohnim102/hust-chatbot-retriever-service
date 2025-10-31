# Multi-stage optimized Dockerfile for a Python microservice (adjust entrypoint as needed)
# - Leverages build-stage to compile wheels and reduce final image size
# - Runs as non-root user, sets sensible PYTHON envs, uses small slim base
# - Caches requirements layer by copying requirements.txt first

# ----- Build stage (wheels/deps) -----
FROM python:3.11-slim AS builder

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Install build dependencies needed for compiling wheels (adjust packages for your deps)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
        libffi-dev \
        ca-certificates \
        curl \
        git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# Copy only requirements first to leverage Docker layer cache
# If you use pyproject/poetry, replace this section accordingly
COPY requirements.txt .

# Upgrade pip and install wheels into a private prefix to copy to runtime
RUN python -m pip install --upgrade pip setuptools wheel \
 && python -m pip install --prefix=/install -r requirements.txt

# ----- Runtime stage -----
FROM python:3.11-slim AS runtime

ARG APP_USER=app
ARG APP_UID=1000
ENV PATH=/usr/local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HEALTHCHECK_PATH=/api/health

# Create non-root user
RUN groupadd -g ${APP_UID} ${APP_USER} \
 && useradd -m -u ${APP_UID} -g ${APP_USER} ${APP_USER} \
 && apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
# Use .dockerignore to exclude unnecessary files (venv, tests, .git, etc.)
COPY --chown=${APP_USER}:${APP_USER} . /app

# Expose default port
EXPOSE ${PORT}
EXPOSE 11434
EXPOSE 6333

# Minimal healthcheck (adjust path/port if needed)
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD curl -f http://127.0.0.1:${PORT}${HEALTHCHECK_PATH} || exit 1

# Switch to non-root user
USER ${APP_USER}

# Default command - adjust to your application entrypoint.
# Common examples:
# - FastAPI/Starlette: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# - Gunicorn (Django/WSGI): ["gunicorn", "myproject.wsgi:application", "-w", "4", "-b", "0.0.0.0:8000"]
# Here we provide a generic fallback that expects the project to supply a start command via CMD override.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]