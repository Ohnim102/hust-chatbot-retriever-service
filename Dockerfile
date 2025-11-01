# Multi-stage optimized Dockerfile for a Python microservice (runs as root)
# - Still uses multi-stage build to minimize final image size
# - Runs with root privileges (no non-root user)

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
        libmagic1 \
        poppler-utils \
        tesseract-ocr \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# Copy only requirements first to leverage Docker layer cache
COPY requirements.txt .

# Upgrade pip and install wheels into a private prefix to copy to runtime
RUN python -m pip install --upgrade pip setuptools wheel \
 && python -m pip install --prefix=/install -r requirements.txt

# ----- Runtime stage -----
FROM python:3.11-slim AS runtime

ARG DEBIAN_FRONTEND=noninteractive
ENV PATH=/usr/local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HEALTHCHECK_PATH=/api/health

# Install runtime dependencies (keep minimal)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        libmagic1 \
        poppler-utils \
        tesseract-ocr \
        tesseract-ocr-vie \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . /app

# Expose ports
EXPOSE ${PORT}
EXPOSE 11434
EXPOSE 6333

# Healthcheck (optional)
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD curl -f http://127.0.0.1:${PORT}${HEALTHCHECK_PATH} || exit 1

# Run as root (no USER directive)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
