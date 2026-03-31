# TN Election Predictor on Hugging Face Spaces

## What changed

This repo now includes a cleaner deployment path for a free Docker Space:

- `backend/app_v2.py` is the new FastAPI entrypoint for deployment.
- `backend/news_fetcher.py` improves RSS parsing and headline cleanup.
- `backend/signal_pipeline.py` adds a hybrid sentiment layer:
  - uses a free multilingual Hugging Face model when available
  - falls back to VADER plus a Tamil lexicon when remote inference is unavailable or too expensive for a large batch
- `backend/predictor.py` loads real constituency metadata so sentiment updates actually affect the matching seat.
- `Dockerfile` now copies `public/` into the runtime image so `tn_assembly.geojson` is available in the Space.

## Recommended Hugging Face Space setup

Create a new Space:

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Choose `Docker`
3. Create the repo

Set these Space secrets or variables:

```bash
HF_TOKEN=your_hf_token
HF_SENTIMENT_MODEL=cardiffnlp/twitter-xlm-roberta-base-sentiment
HF_ENABLE_REMOTE_SENTIMENT=true
HF_REMOTE_CONSTITUENCY_LIMIT=12
```

Notes:

- `HF_TOKEN` is strongly recommended if you want reliable use of Hugging Face Inference API from the Space.
- `HF_REMOTE_CONSTITUENCY_LIMIT=12` keeps full-state refreshes from turning into hundreds of remote inference calls.
- For large update sweeps, the app automatically falls back to the local heuristic sentiment path.

## Local run

```bash
npm install
pip install -r backend/requirements.txt
python -m uvicorn backend.app_v2:app --reload --port 7860
```

## Push to Hugging Face

If you already have a Space created, you can use:

```powershell
./hf_space_push.ps1 -Username "your-username" -SpaceName "tn-election-predictor"
```

Or manually:

```bash
git init
git add .
git commit -m "Deploy election predictor"
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/tn-election-predictor
git push hf main
```

## Suggested next phase

The current implementation is a practical hybrid for a free Space. For a stronger v3, the best next step is:

1. Collect labeled article-to-seat outcomes in a dataset.
2. Fine-tune a lightweight multilingual classifier on Tamil Nadu political headlines.
3. Run periodic calibration jobs that tune Bayesian weights from real validation error instead of fixed heuristics.

If you want, the next step can be turning this into a Hub-ready dataset plus a simple fine-tuning script for a small multilingual transformer.
