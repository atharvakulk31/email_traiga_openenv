# ── Stage 1: Build React frontend ─────────────────────────────────────────────
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --frozen-lockfile 2>/dev/null || npm install

COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python backend ────────────────────────────────────────────────────
FROM python:3.11-slim

# HuggingFace Spaces runs as non-root user 1000
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir aiofiles

# Copy project files
COPY backend/   ./backend/
COPY inference.py ./
COPY openenv.yaml ./

# Copy built frontend static files
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Fix ownership for HF Spaces non-root user
RUN chown -R appuser:appuser /app

USER appuser

ENV PYTHONPATH=/app
# HuggingFace Spaces requires port 7860
ENV PORT=7860

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "backend.main:app", \
     "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
