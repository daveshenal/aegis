# Builder
# Installs all dependencies into a virtual environment.
# Kept separate so the final image doesn't carry build tools.

FROM python:3.11-slim AS builder

WORKDIR /build

# Install system dependencies needed to compile some Python packages
# and WeasyPrint's rendering dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libcairo2 \
    libcairo2-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt


# Runtime
# Copies only the virtual environment and application code.
# No build tools, no cache, minimal attack surface.

FROM python:3.11-slim AS runtime

WORKDIR /app

# Runtime system libraries required by WeasyPrint and Pango
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /venv /venv

# Copy application code
COPY app/ ./app/

# Make venv binaries available without full path
ENV PATH="/venv/bin:$PATH"

# Pydantic settings reads from environment — no .env file in production
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Non-root user for security
RUN useradd --no-create-home --shell /bin/false appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Uvicorn with 2 workers — adjust based on ECS task CPU allocation
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]