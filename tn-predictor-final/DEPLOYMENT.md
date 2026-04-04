# Deployment Guide — TN Election Predictor

## Option A: Hugging Face Spaces (Docker SDK) — Recommended

### 1. Create the Space
1. Go to https://huggingface.co/new-space
2. Settings:
   - **Owner:** your HF username (e.g. `kalilurrahman`)
   - **Space name:** `tn-election-predictor`
   - **SDK:** `Docker`
   - **Visibility:** Public

### 2. Push via Git
```bash
# Clone the empty HF Space
git clone https://huggingface.co/spaces/<your-username>/tn-election-predictor
cd tn-election-predictor

# Copy your project files in
cp -r /path/to/tn-predictor-final/* .

# Commit and push
git add .
git commit -m "Initial deployment"
git push
```

### 3. First Launch
- Spaces will run `docker build` — this downloads transformer models (~1.6 GB) at build time.
- Build takes ~10–15 min on free CPU tier.
- Once live, the app is available at:  
  `https://<your-username>-tn-election-predictor.hf.space`

---

## Option B: Automated Deploy via GitHub Actions

### Prerequisites
- GitHub repo with your project code
- Hugging Face account with a Space already created (Step A1 above)
- HF write token: https://huggingface.co/settings/tokens

### Setup GitHub Secrets
In your GitHub repo → Settings → Secrets and Variables → Actions:

| Secret Name | Value |
|------------|-------|
| `HF_TOKEN` | Your HuggingFace write token |
| `HF_SPACE` | `kalilurrahman/tn-election-predictor` |

### Workflow behaviour
| Event | Action |
|-------|--------|
| PR to `main` | Lint + import validation only |
| Push to `main` | Lint → validate → deploy to HF Space |

---

## Option C: Local Docker

```bash
# Build and run
docker compose up --build

# App available at http://localhost:7860

# Stop
docker compose down
```

Data files in `./data/` persist across container restarts via volume mount.

---

## Option D: Plain Python (No Docker)

```bash
python -m venv venv
source venv/bin/activate          # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python app.py
# → http://127.0.0.1:7860
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `GRADIO_SERVER_PORT` | `7860` | Port Gradio listens on |
| `GRADIO_SERVER_NAME` | `0.0.0.0` | Bind address |
| `TRANSFORMERS_CACHE` | `~/.cache/huggingface` | Model cache directory |
| `HF_HUB_DISABLE_TELEMETRY` | `0` | Set to `1` in dev |

---

## Resource Requirements

| Tier | RAM | Disk | Notes |
|------|-----|------|-------|
| HF Free CPU | 16 GB | 50 GB | Slow inference (~5–10s/request) |
| HF CPU Upgrade | 32 GB | 50 GB | Recommended for production |
| Local | 8 GB+ | 10 GB+ | GPU optional, models run on CPU |

> **Model sizes:**  
> `cardiffnlp/twitter-roberta-base-sentiment-latest` ≈ 500 MB  
> `facebook/bart-large-mnli` ≈ 1.6 GB
