# ============================================================
# TN Election Predictor 2026 — Multi-stage Docker Build
# Targets: Hugging Face Spaces (port 7860) / any Docker host
# ============================================================

# Stage 1: Build React frontend
FROM node:20-slim AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Python/FastAPI runtime
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend build
COPY --from=build-stage /app/dist ./dist

# Copy backend source
COPY backend ./backend
COPY public ./public

# Create non-root user for Hugging Face Spaces compatibility
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Hugging Face uses 7860; override with PORT env var for other hosts
EXPOSE 7860
ENV PORT=7860
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:${PORT}/api/health || exit 1

CMD ["python", "-m", "uvicorn", "backend.app_v2:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
