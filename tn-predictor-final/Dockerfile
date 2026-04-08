# ─────────────────────────────────────────────────────────────
# TN Election Predictor 2026 — Hugging Face Spaces Dockerfile
# Stack: React 19 (Vite) + FastAPI + Uvicorn
# Port:  7860 (HF Spaces requirement)
# ─────────────────────────────────────────────────────────────

# ── Stage 1: Build the React frontend ────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /build

# Copy package files first for layer caching
COPY package.json package-lock.json ./
RUN npm ci --prefer-offline

# Copy all source and config files
COPY index.html vite.config.ts tsconfig.json tsconfig.app.json tsconfig.node.json ./
COPY postcss.config.js tailwind.config.js eslint.config.js ./
COPY src/ ./src/
COPY public/ ./public/

# Build production bundle → /build/dist
RUN npm run build

# ── Stage 2: Python runtime ───────────────────────────────────
FROM python:3.11-slim

# HF Spaces non-root user requirement
RUN useradd -m -u 1000 appuser

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy built React frontend from stage 1
COPY --from=frontend-builder /build/dist ./dist/

# Copy public data files (GeoJSON, CSVs, JSONs used by the API)
COPY public/ ./public/

# Create writable data dir
RUN mkdir -p /app/data && chown -R appuser:appuser /app

ENV PORT=7860
ENV ADMIN_ACCESS_KEY=KRKRKR

USER appuser

EXPOSE 7860

# Run FastAPI — it serves both the API and the React SPA
CMD ["python", "-m", "uvicorn", "backend.app_v2:app", "--host", "0.0.0.0", "--port", "7860"]
