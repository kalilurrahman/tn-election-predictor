#!/bin/bash
# TN Election Predictor 2026 — One-click deploy script
set -e

echo "=================================="
echo " TN Election Predictor 2026"
echo " Deploy Script"
echo "=================================="

MODE=${1:-"local"}

if [ "$MODE" = "local" ]; then
  echo "▶ Starting local development..."
  echo ""
  echo "  Installing npm packages..."
  npm install
  echo "  Installing Python packages..."
  pip install -r backend/requirements.txt
  echo ""
  echo "  Starting backend on :7860 ..."
  python -m uvicorn backend.app_v2:app --reload --port 7860 &
  BACKEND_PID=$!
  echo "  Backend PID: $BACKEND_PID"
  sleep 2
  echo "  Starting frontend on :6001 ..."
  npm run dev &
  echo ""
  echo "  ✅ App running at http://localhost:6001"
  echo "  ✅ API docs at  http://localhost:7860/docs"
  echo ""
  echo "  Press Ctrl+C to stop both servers"
  wait

elif [ "$MODE" = "docker" ]; then
  echo "▶ Building Docker image..."
  docker build -t tn-election-predictor:latest .
  echo "▶ Running container on port 7860..."
  docker run -d -p 7860:7860 --name tn-predictor tn-election-predictor:latest
  echo "✅ Running at http://localhost:7860"

elif [ "$MODE" = "hf" ]; then
  if [ -z "$HF_USERNAME" ]; then
    echo "Set HF_USERNAME env var first: export HF_USERNAME=your_username"
    exit 1
  fi
  echo "▶ Pushing to Hugging Face Spaces..."
  git remote add hf https://huggingface.co/spaces/$HF_USERNAME/tn-election-predictor 2>/dev/null || true
  git add -A
  git commit -m "Update: $(date '+%Y-%m-%d %H:%M')" || true
  git push hf main
  echo "✅ Deployed to https://huggingface.co/spaces/$HF_USERNAME/tn-election-predictor"

elif [ "$MODE" = "build" ]; then
  echo "▶ Building production frontend..."
  npm install
  npm run build
  echo "✅ Build complete in dist/"

else
  echo "Usage: ./deploy.sh [local|docker|hf|build]"
fi
