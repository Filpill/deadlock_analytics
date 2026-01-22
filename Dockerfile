# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (git needed for deadlock-api-client)
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies using uv (frozen lockfile, no dev dependencies)
RUN uv sync --frozen --no-dev

# Copy application code
COPY app.py ./
COPY templates ./templates/
COPY static ./static/

# Cloud Run expects the app to listen on $PORT (default 8080)
# Gunicorn will use PORT env variable or fallback to 8000
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

# Run gunicorn with Cloud Run optimized settings
# - Bind to 0.0.0.0:$PORT
# - Use 2 workers (Cloud Run handles scaling via container instances)
# - 120s timeout for long API requests
# - Graceful timeout for shutdown
CMD exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --graceful-timeout 30 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    app:app
