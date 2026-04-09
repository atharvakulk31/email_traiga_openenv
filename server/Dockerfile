# server/Dockerfile — required by OpenEnv environment structure spec.
#
# This is a thin wrapper that delegates to the project's primary Dockerfile
# at the repository root. The HuggingFace Space build still uses the root
# Dockerfile; this file exists to satisfy openenv validate_env_structure().

FROM python:3.11-slim

# HuggingFace Spaces runs as non-root user 1000
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install system deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl && \
    rm -rf /var/lib/apt/lists/*

# Copy project
COPY ../requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt && \
    pip install --no-cache-dir aiofiles

COPY .. /app/

RUN chown -R appuser:appuser /app
USER appuser

ENV PYTHONPATH=/app
ENV PORT=7860

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
