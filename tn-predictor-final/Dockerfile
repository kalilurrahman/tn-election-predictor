FROM node:20-slim AS frontend-build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY tsconfig*.json ./
COPY vite.config.ts ./
COPY index.html ./
COPY postcss.config.js ./
COPY tailwind.config.js ./
COPY eslint.config.js ./
COPY src ./src
COPY public ./public

RUN npm run build

FROM python:3.10-slim

RUN useradd -m -u 1000 appuser

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .
COPY --from=frontend-build /app/dist ./dist

RUN mkdir -p /app/data /app/data/processed && chown -R appuser:appuser /app/data

ENV PORT=7860
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

USER appuser

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "backend.app_v2:app", "--host", "0.0.0.0", "--port", "7860"]
