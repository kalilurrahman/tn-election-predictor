import os, json, asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from backend.scraper import NewsScraper
from backend.sentiment import SentimentEngine
from backend.bayesian import BayesianPredictor

app = FastAPI(title="TN Election Predictor 2026 API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

scraper = NewsScraper()
sentiment_engine = SentimentEngine()
bayesian = BayesianPredictor()

# --- In-Memory State ---
cache: Dict[str, Dict] = {}
CACHE_TTL = timedelta(hours=1)
update_status = {
    "running": False,
    "last_run": None,
    "last_run_duration": None,
    "constituencies_updated": 0,
    "total_constituencies": 234,
    "progress": 0,
    "log": []
}

def log_update(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    update_status["log"].append(f"[{ts}] {msg}")
    if len(update_status["log"]) > 100:
        update_status["log"] = update_status["log"][-100:]
    print(msg)

def get_cached(key: str):
    if key in cache:
        e = cache[key]
        if datetime.now() - e["timestamp"] < CACHE_TTL:
            return e["data"]
    return None

def set_cache(key: str, data: Any):
    cache[key] = {"data": data, "timestamp": datetime.now()}

# --- Models ---
class UpdateTriggerRequest(BaseModel):
    constituencies: Optional[List[str]] = None  # None = all
    force_refresh: bool = False

# --- API Endpoints ---
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "version": "2.0.0",
        "last_update": update_status["last_run"],
        "model": "Bayesian + VADER Sentiment",
        "constituencies": 234
    }

@app.get("/api/news/{constituency_name}/{district_name}")
async def get_news(constituency_name: str, district_name: str):
    cache_key = f"news_{constituency_name}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    news_items = scraper.get_constituency_news(constituency_name, district_name)
    processed = []
    total_sentiment = 0.0

    for item in news_items:
        score = sentiment_engine.analyze_text(item["title"])
        label = sentiment_engine.get_sentiment_label(score)
        processed.append({**item, "sentiment_score": round(score, 2), "sentiment_label": label})
        total_sentiment += score

    avg = total_sentiment / len(processed) if processed else 0.0
    result = {
        "constituency": constituency_name,
        "district": district_name,
        "news": processed,
        "average_sentiment": round(avg, 2),
        "overall_label": sentiment_engine.get_sentiment_label(avg),
        "last_updated": datetime.now().isoformat()
    }
    set_cache(cache_key, result)
    return result

@app.get("/api/constituencies")
async def get_constituencies():
    targets = [
        os.path.join(os.getcwd(), "dist", "constituencies.json"),
        os.path.join(os.getcwd(), "public", "constituencies.json")
    ]
    for t in targets:
        if os.path.exists(t):
            return FileResponse(t)
    raise HTTPException(status_code=404, detail="Constituency data not found.")

@app.get("/api/predictions/summary")
async def get_predictions_summary():
    """Returns aggregate seat predictions with Bayesian confidence intervals."""
    cached = get_cached("summary")
    if cached:
        return cached
    result = bayesian.get_summary()
    set_cache("summary", result)
    return result

@app.get("/api/predictions/{ac_no}")
async def get_constituency_prediction(ac_no: int):
    """Returns Bayesian prediction for a single constituency."""
    cached = get_cached(f"pred_{ac_no}")
    if cached:
        return cached
    result = bayesian.get_constituency_prediction(ac_no)
    if not result:
        raise HTTPException(status_code=404, detail=f"AC #{ac_no} not found")
    set_cache(f"pred_{ac_no}", result)
    return result

@app.get("/api/neck-and-neck")
async def get_neck_and_neck():
    """Returns constituencies where margin < 3%."""
    cached = get_cached("neck_and_neck")
    if cached:
        return cached
    result = bayesian.get_neck_and_neck_seats()
    set_cache("neck_and_neck", result)
    return result

@app.get("/api/surprises")
async def get_surprise_seats():
    """Returns constituencies with high upset probability."""
    cached = get_cached("surprises")
    if cached:
        return cached
    result = bayesian.get_surprise_seats()
    set_cache("surprises", result)
    return result

# --- Manual Update Trigger ---
@app.post("/api/admin/trigger-update")
async def trigger_update(req: UpdateTriggerRequest, background_tasks: BackgroundTasks):
    """Manual trigger to run sentiment analysis + Bayesian update."""
    if update_status["running"]:
        return JSONResponse({"status": "already_running", "message": "Update already in progress"}, status_code=409)

    update_status["running"] = True
    update_status["progress"] = 0
    update_status["log"] = []
    update_status["constituencies_updated"] = 0
    background_tasks.add_task(run_update_job, req.constituencies, req.force_refresh)
    return {"status": "started", "message": "Update job started in background"}

@app.get("/api/admin/update-status")
async def get_update_status():
    """Poll this endpoint to track update progress."""
    return update_status

@app.post("/api/admin/clear-cache")
async def clear_cache():
    """Clear all cached results, forcing fresh fetches."""
    cache.clear()
    return {"status": "ok", "message": "Cache cleared"}

async def run_update_job(target_constituencies: Optional[List[str]], force: bool):
    """Background job: scrape news → sentiment → update Bayesian model."""
    start = datetime.now()
    log_update("=== UPDATE JOB STARTED ===")

    try:
        # Load constituency list
        data_path = os.path.join(os.getcwd(), "public", "constituencies.json")
        if os.path.exists(data_path):
            with open(data_path) as f:
                constituencies = json.load(f)
        else:
            constituencies = [{"name": f"Constituency #{i}", "district": "Tamil Nadu"} for i in range(1, 235)]

        targets = constituencies
        if target_constituencies:
            targets = [c for c in constituencies if c.get("name") in target_constituencies]

        total = len(targets)
        log_update(f"Processing {total} constituencies...")

        for idx, c in enumerate(targets):
            name = c.get("name", "Unknown")
            district = c.get("district", "Tamil Nadu")

            if not force and get_cached(f"news_{name}"):
                log_update(f"[{idx+1}/{total}] Skipping {name} (cached)")
            else:
                try:
                    log_update(f"[{idx+1}/{total}] Scraping {name}...")
                    news_items = scraper.get_constituency_news(name, district)
                    scores = [sentiment_engine.analyze_text(it["title"]) for it in news_items]
                    avg_score = sum(scores) / len(scores) if scores else 0.0

                    # Feed into Bayesian updater
                    bayesian.apply_sentiment_update(name, avg_score, weight=0.6)
                    log_update(f"  → Sentiment: {avg_score:.2f} | News items: {len(news_items)}")

                    result = {
                        "constituency": name, "district": district,
                        "news": [{**it, "sentiment_score": round(sentiment_engine.analyze_text(it["title"]), 2),
                                  "sentiment_label": sentiment_engine.get_sentiment_label(sentiment_engine.analyze_text(it["title"]))} for it in news_items],
                        "average_sentiment": round(avg_score, 2),
                        "overall_label": sentiment_engine.get_sentiment_label(avg_score),
                        "last_updated": datetime.now().isoformat()
                    }
                    cache[f"news_{name}"] = {"data": result, "timestamp": datetime.now()}

                    # Small delay to be polite to the news API
                    await asyncio.sleep(0.3)
                except Exception as e:
                    log_update(f"  ✗ Error for {name}: {e}")

            update_status["constituencies_updated"] = idx + 1
            update_status["progress"] = round((idx + 1) / total * 100)

        # Invalidate summary cache so it recalculates
        for key in ["summary", "neck_and_neck", "surprises"]:
            if key in cache:
                del cache[key]

        elapsed = (datetime.now() - start).total_seconds()
        update_status["last_run"] = datetime.now().isoformat()
        update_status["last_run_duration"] = f"{elapsed:.1f}s"
        log_update(f"=== UPDATE COMPLETE in {elapsed:.1f}s ===")

    except Exception as e:
        log_update(f"FATAL ERROR: {e}")
    finally:
        update_status["running"] = False

# --- Static File Serving ---
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dist_path = os.path.join(base_dir, "dist")

if os.path.exists(dist_path):
    assets_path = os.path.join(dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/tn_assembly.geojson")
    async def serve_geojson():
        return FileResponse(os.path.join(dist_path, "tn_assembly.geojson"))

    @app.get("/constituencies.json")
    async def serve_constituencies_json():
        return FileResponse(os.path.join(dist_path, "constituencies.json"))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(dist_path, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_path, "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "Run 'npm run build' first to generate the dist/ folder."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
