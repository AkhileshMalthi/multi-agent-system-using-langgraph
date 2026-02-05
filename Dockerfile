# --- Stage 1: Build ---
FROM python:3.13-slim AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1

# Install system dependencies (needed for Postgres driver)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Use a non-root directory for the app
WORKDIR /app

# Install dependencies first (leverage Docker layer caching)
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the source code
COPY . /app

# Install the project
RUN uv sync --frozen --no-dev


# --- Stage 2: Runtime ---
FROM python:3.13-slim

# Install runtime dependencies (needed for Postgres driver)
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the virtual environment from the build stage
COPY --from=build /app/.venv /app/.venv

# Copy application code
COPY --from=build /app/src ./src
COPY --from=build /app/.env.example .

# Create directory for logs
RUN mkdir -p logs

# Ensure the app uses the virtual environment automatically
ENV PATH="/app/.venv/bin:$PATH"
# Set Python path so 'src' modules are discoverable
ENV PYTHONPATH=/app/src

# Default command (will be overridden in docker-compose)
# Note: Replace this with your actual entry point once you create it
CMD ["python", "-c", "print('Container is ready. Configure your entry point.')"]