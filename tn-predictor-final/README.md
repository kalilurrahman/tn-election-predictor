---
title: TN Election Predictor 2026
emoji: 🗳️
colorFrom: red
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# TN Election Predictor 2026

> AI-Powered Psephology Dashboard for the 2026 Tamil Nadu Legislative Assembly Elections

**Stack:** React 19 + TypeScript + Tailwind · FastAPI + Uvicorn · Bayesian Model · VADER Sentiment · Leaflet Maps

---

## Architecture

The app now uses a formal 5-layer election-forecast architecture:
1. Data ingestion
2. Feature engineering
3. Prediction engine
4. Forecasting/simulation
5. Analytics UI

See `SYSTEM_ARCHITECTURE.md` for full details and implementation roadmap.

## Features

| Feature | Description |
|---|---|
| 🗺️ **Battleground Map** | Real 234-constituency TopoJSON map, coloured by predicted winner |
| 📊 **State Assembly Projection** | Live seat tally with Magic Number (118) tracker |
| 🎛️ **Strategy Simulator** | Swing sliders for SPA/NDA/TVK/NTK — re-runs full 234-seat model live |
| 🔍 **Constituency Deep-Dive** | Candidate profiles, issues, Bayesian win probability, sentiment trend |
| 📰 **Live Buzz Tab** | Real-time Google News scraping with Tamil/English sentiment scoring |
| 🤖 **Admin Update Panel** | Manual trigger to re-scrape all 234 constituencies and update Bayesian model |
| 🎯 **Neck-and-Neck Tracker** | `/api/neck-and-neck` — seats with < 3% margin |
| 💥 **Surprise Detector** | `/api/surprises` — upsets where trailing candidate has 25–45% chance |

---

## API Endpoints

```
GET  /api/health                           Health check
GET  /api/constituencies                   Full 234-constituency data
GET  /api/predictions/summary              State-level seat tally
GET  /api/predictions/{ac_no}              Per-seat Bayesian prediction
GET  /api/neck-and-neck                    Closest margin seats
GET  /api/surprises                        High upset-risk seats
GET  /api/news/{constituency}/{district}   Live news + sentiment
GET  /api/admin/update-status              Poll update progress

POST /api/admin/trigger-update             Start update job
     Body: { "force_refresh": false }
POST /api/admin/clear-cache                Wipe all cached results
```

---

## Deployment Options

### Option 1: Hugging Face Spaces (FREE — Recommended)

1. Create a new Space at https://huggingface.co/new-space
2. Select **Docker** as the SDK
3. Push this repo:
   ```bash
   git init
   git add .
   git commit -m "Initial deploy"
   git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/tn-election-predictor
   git push hf main
   ```
4. The Space will auto-build and serve at `https://YOUR_USERNAME-tn-election-predictor.hf.space`

> **Port:** Hugging Face Docker Spaces expose port 7860 by default — already configured.

---

### Option 2: Docker (any host — Railway, Fly.io, Render, VPS)

```bash
# Build and run locally
docker build -t tn-predictor .
docker run -p 7860:7860 tn-predictor

# With docker-compose
docker-compose up --build

# Deploy to Railway (free tier available)
# Install Railway CLI: npm install -g @railway/cli
railway login
railway init
railway up
```

---

### Option 3: Lovable (Frontend only)

Lovable deploys the React frontend only — the FastAPI backend won't run.
Use this mode for a static demo with simulated predictions (no live news/sentiment).

1. Upload the `src/` folder to Lovable
2. Set all API calls to use mock data (see `src/data/constituencies2026.ts`)
3. Deploy via Lovable's one-click deploy

---

### Option 4: GitHub Pages (Static / Frontend only)

```bash
# Build for static deployment
npm run build

# Deploy dist/ to GitHub Pages
npm install -g gh-pages
gh-pages -d dist
```

> Note: Live news/sentiment features require the Python backend. GitHub Pages serves static files only.

---

## Local Development

```bash
# 1. Install frontend deps
npm install

# 2. Install backend deps
pip install -r backend/requirements.txt

# 3. Run backend (terminal 1)
python -m uvicorn backend.main:app --reload --port 7860

# 4. Run frontend dev server (terminal 2)
npm run dev
# Opens at http://localhost:6001
# Vite proxies /api/* to http://localhost:7860
```

---

## Triggering a Prediction Update

Via the Admin Panel in the UI header, or via API:

```bash
# Trigger update via curl
curl -X POST http://localhost:7860/api/admin/trigger-update \
  -H "Content-Type: application/json" \
  -d '{"force_refresh": false}'

# Poll progress
curl http://localhost:7860/api/admin/update-status

# Force refresh (ignores cache)
curl -X POST http://localhost:7860/api/admin/trigger-update \
  -d '{"force_refresh": true}'
```

The update job:
1. Scrapes Google News RSS for each of the 234 constituencies
2. Runs VADER + Tamil lexicon sentiment analysis on headlines
3. Feeds sentiment scores into the Bayesian model as logit-space updates
4. Invalidates cached predictions so the UI fetches fresh data

---

## Architecture

```
Browser (React)
    │
    ├── /                    → Static SPA (Vite build)
    ├── /api/news/...        → FastAPI → NewsScraper → SentimentEngine
    ├── /api/predictions/... → FastAPI → BayesianPredictor
    └── /api/admin/...       → FastAPI → Background update job
                                           │
                               ┌───────────┘
                               │  BayesianPredictor
                               │  (logit-space Bayesian updates)
                               │  ← sentiment signals
                               │  ← prior from 2021 ECI results
                               └───────────────────────────────
```

---

## Credits

Built with [Antigravity](https://antigravity.dev) + [Claude](https://claude.ai) by Anthropic.

Data sources: ECI 2021 Results · Wikipedia Alliance Data (March 2026) · Google News RSS

Refresh marker: 2026-03-31 IST
