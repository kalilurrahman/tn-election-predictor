# ─────────────────────────────────────────────────────────────
# TN Election Predictor — Hugging Face Spaces Dockerfile
# SDK: Docker  |  Hardware: CPU (free tier compatible)
# ─────────────────────────────────────────────────────────────

FROM python:3.10-slim

# HF Spaces runs as a non-root user; create one
RUN useradd -m -u 1000 appuser

WORKDIR /app

# ── System deps ──────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# ── Python deps (cached layer) ───────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── App source ───────────────────────────────────────────────
COPY --chown=appuser:appuser . .

# Create writable data dir for JSON persistence
RUN mkdir -p /app/data && chown appuser:appuser /app/data

# HF Spaces expects the app to listen on port 7860
ENV GRADIO_SERVER_PORT=7860
ENV GRADIO_SERVER_NAME=0.0.0.0

# Pre-download transformer models at build time
# (avoids cold-start timeout on free-tier Spaces)
# Comment out if you prefer lazy loading at first run.
RUN python -c "\
from transformers import pipeline; \
print('Downloading sentiment model...'); \
pipeline('sentiment-analysis', model='cardiffnlp/twitter-roberta-base-sentiment-latest', device=-1); \
print('Downloading zero-shot model...'); \
pipeline('zero-shot-classification', model='facebook/bart-large-mnli', device=-1); \
print('Models ready.')"

USER appuser

EXPOSE 7860

CMD ["python", "app.py"]
