import asyncio
import json
import os
import io
import csv
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.news_fetcher import NewsScraper
from backend.predictor import BayesianPredictor
from backend.signal_pipeline import SentimentEngine
from backend.insights import ConstituencyInsightsEngine
from backend.candidate_sync import CandidateSyncEngine
from backend.source_registry import get_candidate_sync_presets

app = FastAPI(title="TN Election Predictor 2026 API", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_PATH = os.path.join(BASE_DIR, "dist")
PUBLIC_PATH = os.path.join(BASE_DIR, "public")

scraper = NewsScraper()
sentiment_engine = SentimentEngine()
insights_engine = ConstituencyInsightsEngine()
candidate_sync_engine = CandidateSyncEngine(BASE_DIR)
bayesian = BayesianPredictor(data_path=os.path.join(PUBLIC_PATH, "constituencies.json"))

cache: Dict[str, Dict] = {}
CACHE_TTL = timedelta(hours=1)

update_status = {
    "running": False,
    "last_run": None,
    "last_run_duration": None,
    "constituencies_updated": 0,
    "total_constituencies": 234,
    "progress": 0,
    "log": [],
}
candidate_sync_status = {
    "running": False,
    "last_run": None,
    "last_result": None,
}


class UpdateTriggerRequest(BaseModel):
    constituencies: Optional[List[str]] = None
    force_refresh: bool = False


class SimulationRunRequest(BaseModel):
    scenario_type: str = "baseline"
    custom_swing: Optional[Dict[str, float]] = None


class CandidateSyncRequest(BaseModel):
    source_urls: Optional[List[str]] = None


def log_update(message: str):
    stamp = datetime.now().strftime("%H:%M:%S")
    update_status["log"].append(f"[{stamp}] {message}")
    update_status["log"] = update_status["log"][-100:]
    print(message)


def get_cached(key: str):
    if key not in cache:
        return None
    entry = cache[key]
    if datetime.now() - entry["timestamp"] < CACHE_TTL:
        return entry["data"]
    return None


def set_cache(key: str, data: Any):
    cache[key] = {"data": data, "timestamp": datetime.now()}


def refresh_bayesian_model():
    global bayesian
    curated_path = find_file("constituencies_curated.json")
    source_path = curated_path or os.path.join(PUBLIC_PATH, "constituencies.json")
    bayesian = BayesianPredictor(data_path=source_path)


def find_file(filename: str) -> Optional[str]:
    for root in (DIST_PATH, PUBLIC_PATH):
        candidate = os.path.join(root, filename)
        if os.path.exists(candidate):
            return candidate
    return None


refresh_bayesian_model()


def load_constituencies() -> List[Dict]:
    curated_path = find_file("constituencies_curated.json")
    data_path = curated_path or find_file("constituencies.json")
    if data_path:
        with open(data_path, encoding="utf-8") as handle:
            rows = json.load(handle)
        return candidate_sync_engine.align_with_geojson(rows)
    return [{"acNo": i, "name": f"Constituency #{i}", "district": "Tamil Nadu"} for i in range(1, 235)]


def normalize_tn_label(value: str) -> str:
    text = (value or "").strip()
    if text.lower() in {"tn", "t.n.", "tamilnadu"}:
        return "Tamil Nadu"
    return text


def build_candidate_rows(constituencies: List[Dict]) -> List[Dict]:
    rows: List[Dict] = []
    for constituency in constituencies:
        ac_no = int(constituency.get("acNo", 0) or 0)
        ac_name = constituency.get("name", f"AC #{ac_no}")
        district = normalize_tn_label(str(constituency.get("district", "Tamil Nadu")))
        region = constituency.get("region", "STATE")
        reserved_for = constituency.get("reservedFor", "GEN")
        prediction = constituency.get("prediction", {})

        for candidate in constituency.get("candidates2026", []):
            row = {
                "ac_no": ac_no,
                "ac_name": ac_name,
                "district": district,
                "state": "Tamil Nadu",
                "region": region,
                "reserved_for": reserved_for,
                "candidate_name": candidate.get("name"),
                "party": candidate.get("party"),
                "alliance": candidate.get("alliance", "OTHERS"),
                "is_incumbent": bool(candidate.get("isIncumbent", candidate.get("is_incumbent", False))),
                "education": candidate.get("education"),
                "profession": candidate.get("profession"),
                "age": candidate.get("age"),
                "gender": candidate.get("gender"),
                "assets": candidate.get("assets"),
                "liabilities": candidate.get("liabilities"),
                "criminal_cases": candidate.get("cases"),
                "literacy": candidate.get("literacy"),
                "community": candidate.get("community"),
                "eci_approved": bool(candidate.get("eciApproved", candidate.get("eci_approved", False))),
                "party_approved": bool(candidate.get("partyApproved", candidate.get("party_approved", False))),
                "nomination_status": candidate.get("nominationStatus", candidate.get("nomination_status", "unknown")),
                "nomination_date": candidate.get("nominationDate", candidate.get("nomination_date")),
                "affidavit_url": candidate.get("affidavitUrl", candidate.get("affidavit_url")),
                "eci_candidate_id": candidate.get("eciCandidateId", candidate.get("eci_candidate_id")),
                "contact": candidate.get("contact"),
                "website": candidate.get("website"),
                "x_handle": candidate.get("xHandle", candidate.get("x_handle")),
                "is_rerunner": bool(candidate.get("isRerunner", candidate.get("is_rerunner", False))),
                "is_celebrity": bool(candidate.get("isCelebrity", candidate.get("is_celebrity", False))),
                "validation_reports": candidate.get("validationReports", candidate.get("validation_reports", [])),
                "source": candidate.get("source", "curated"),
                "predicted_winner": prediction.get("predictedWinner"),
            }
            rows.append(row)
    return rows


def get_constituency_context(constituency_name: str) -> Dict:
    normalized = constituency_name.replace(" TN", " Tamil Nadu").replace(" tn", " tamil nadu")
    lowered = constituency_name.lower().strip()
    lowered_norm = normalized.lower().strip()
    for constituency in load_constituencies():
        name = str(constituency.get("name", "")).lower().strip()
        if lowered == name or lowered in name or name in lowered or lowered_norm == name:
            return constituency
    return {}


def build_news_result(
    constituency_name: str,
    district_name: str,
    prefer_remote: bool = True,
) -> Dict:
    context = get_constituency_context(constituency_name)
    issues = context.get("keyIssues", [])
    candidates = [candidate.get("name", "") for candidate in context.get("candidates2026", [])]
    district = context.get("district", district_name)
    if isinstance(district, str) and district.strip().lower() in {"tn", "t.n.", "tamilnadu"}:
        district = "Tamil Nadu"

    news_items = scraper.get_constituency_news(constituency_name, district)
    analyzed = sentiment_engine.analyze_news(
        news_items,
        constituency_name=constituency_name,
        district_name=district,
        issues=issues,
        candidates=candidates,
        prefer_remote=prefer_remote,
    )

    return {
        "constituency": constituency_name,
        "district": district,
        "news": analyzed["news"],
        "average_sentiment": analyzed["average_sentiment"],
        "overall_label": analyzed["overall_label"],
        "average_confidence": analyzed["average_confidence"],
        "article_count": analyzed["article_count"],
        "source_diversity": analyzed["source_diversity"],
        "average_hours_old": analyzed["average_hours_old"],
        "signal_strength": analyzed["signal_strength"],
        "sentiment_backend": analyzed["sentiment_backend"],
        "sentiment_model": analyzed["sentiment_model"],
        "last_updated": datetime.now().isoformat(),
    }


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "version": "2.1.0",
        "last_update": update_status["last_run"],
        "model": "Bayesian + Hybrid HF/VADER Sentiment",
        "sentiment_model": sentiment_engine.remote_client.model,
        "remote_sentiment_enabled": sentiment_engine.remote_client.enabled,
        "constituencies": 234,
    }


@app.get("/api/news/{constituency_name}/{district_name}")
async def get_news(constituency_name: str, district_name: str):
    cache_key = f"news_{constituency_name.lower().strip()}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    result = build_news_result(constituency_name, district_name, prefer_remote=True)
    set_cache(cache_key, result)
    return result


@app.get("/api/constituencies")
async def get_constituencies():
    data_path = find_file("constituencies_curated.json") or find_file("constituencies.json")
    if not data_path:
        raise HTTPException(status_code=404, detail="Constituency data not found.")
    return FileResponse(data_path)


@app.get("/api/predictions/summary")
async def get_predictions_summary():
    cached = get_cached("summary")
    if cached:
        return cached
    result = bayesian.get_summary()
    set_cache("summary", result)
    return result


@app.get("/api/predictions/{ac_no}")
async def get_constituency_prediction(ac_no: int):
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
    cached = get_cached("neck_and_neck")
    if cached:
        return cached
    result = bayesian.get_neck_and_neck_seats()
    set_cache("neck_and_neck", result)
    return result


@app.get("/api/surprises")
async def get_surprise_seats():
    cached = get_cached("surprises")
    if cached:
        return cached
    result = bayesian.get_surprise_seats()
    set_cache("surprises", result)
    return result


@app.get("/api/analytics/constituency/{ac_no}")
async def get_constituency_analytics(ac_no: int):
    cache_key = f"analytics_ac_{ac_no}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    snapshot = insights_engine.get_constituency_snapshot(load_constituencies(), ac_no=ac_no)
    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Constituency AC #{ac_no} not found")
    set_cache(cache_key, snapshot)
    return snapshot


@app.get("/api/analytics/constituency-by-name/{constituency_name:path}")
async def get_constituency_analytics_by_name(constituency_name: str):
    cache_key = f"analytics_name_{constituency_name.lower().strip()}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    snapshot = insights_engine.get_constituency_snapshot(load_constituencies(), name=constituency_name)
    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Constituency '{constituency_name}' not found")
    set_cache(cache_key, snapshot)
    return snapshot


@app.get("/api/analytics/party-trends")
async def get_party_trends():
    cached = get_cached("party_trends")
    if cached:
        return cached
    trends = insights_engine.get_party_trends(load_constituencies())
    set_cache("party_trends", trends)
    return trends


@app.get("/api/candidates")
async def get_candidates(
    ac_no: Optional[int] = None,
    constituency: Optional[str] = None,
    only_approved: bool = False,
):
    rows = build_candidate_rows(load_constituencies())
    if ac_no is not None:
        rows = [row for row in rows if int(row.get("ac_no", 0)) == ac_no]
    if constituency:
        lowered = constituency.lower().strip()
        rows = [row for row in rows if lowered in str(row.get("ac_name", "")).lower()]
    if only_approved:
        rows = [row for row in rows if row.get("eci_approved") or row.get("party_approved")]

    return {
        "count": len(rows),
        "approved_count": sum(1 for row in rows if row.get("eci_approved") or row.get("party_approved")),
        "rows": rows,
    }


@app.get("/api/candidates/export.csv")
async def export_candidates_csv(
    only_approved: bool = False,
):
    rows = build_candidate_rows(load_constituencies())
    if only_approved:
        rows = [row for row in rows if row.get("eci_approved") or row.get("party_approved")]

    columns = [
        "ac_no", "ac_name", "district", "state", "region", "reserved_for",
        "candidate_name", "party", "alliance", "is_incumbent", "education", "profession", "age", "gender",
        "assets", "liabilities", "criminal_cases", "literacy", "community",
        "eci_approved", "party_approved", "nomination_status", "nomination_date",
        "affidavit_url", "eci_candidate_id", "contact", "website", "x_handle", "source", "predicted_winner",
        "is_rerunner", "is_celebrity", "validation_reports",
    ]

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in columns})

    from fastapi.responses import Response

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tn_candidates_2026.csv"},
    )


@app.get("/api/simulations/types")
async def get_simulation_types():
    return {"types": insights_engine.get_simulation_types()}


@app.get("/api/elections/history")
async def get_election_history():
    path = find_file("tn_assembly_history.json")
    if not path:
        raise HTTPException(status_code=404, detail="Election history dataset not found")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


@app.get("/api/elections/community-split")
async def get_constituency_community_split(ac_no: Optional[int] = None):
    path = find_file("tn_constituency_community_split.json")
    if not path:
        raise HTTPException(status_code=404, detail="Community split dataset not found")
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    rows = payload.get("rows", [])
    if ac_no is not None:
        rows = [row for row in rows if int(row.get("ac_no", 0)) == ac_no]
    return {
        "state": payload.get("state", "Tamil Nadu"),
        "source_note": payload.get("source_note", ""),
        "count": len(rows),
        "rows": rows,
    }


@app.post("/api/simulations/run")
async def run_simulation(req: SimulationRunRequest):
    return insights_engine.run_simulation(
        load_constituencies(),
        scenario_type=req.scenario_type,
        custom=req.custom_swing or {},
    )


@app.get("/api/admin/candidate-sync/status")
async def get_candidate_sync_status():
    return candidate_sync_status


@app.post("/api/admin/candidate-sync")
async def trigger_candidate_sync(req: CandidateSyncRequest):
    if candidate_sync_status["running"]:
        return JSONResponse(
            {"status": "already_running", "message": "Candidate sync already in progress"},
            status_code=409,
        )

    candidate_sync_status["running"] = True
    try:
        env_urls = os.getenv("CANDIDATE_SOURCE_URLS", "")
        fallback_urls = [u.strip() for u in env_urls.split(",") if u.strip()]
        source_urls = req.source_urls or fallback_urls
        if not source_urls:
            return JSONResponse(
                {
                    "status": "no_sources",
                    "message": "No candidate source URLs configured. Set CANDIDATE_SOURCE_URLS or pass source_urls in request body.",
                },
                status_code=400,
            )
        result = candidate_sync_engine.run_sync(source_urls)
        refresh_bayesian_model()
        candidate_sync_status["last_result"] = result
        candidate_sync_status["last_run"] = datetime.now().isoformat()

        cache.clear()
        return result
    finally:
        candidate_sync_status["running"] = False


@app.get("/api/admin/candidate-sync/presets")
async def get_candidate_sync_presets_api():
    return get_candidate_sync_presets()


@app.post("/api/admin/trigger-update")
async def trigger_update(req: UpdateTriggerRequest, background_tasks: BackgroundTasks):
    if update_status["running"]:
        return JSONResponse(
            {"status": "already_running", "message": "Update already in progress"},
            status_code=409,
        )

    update_status["running"] = True
    update_status["progress"] = 0
    update_status["log"] = []
    update_status["constituencies_updated"] = 0
    background_tasks.add_task(run_update_job, req.constituencies, req.force_refresh)
    return {"status": "started", "message": "Update job started in background"}


@app.get("/api/admin/update-status")
async def get_update_status():
    return update_status


@app.post("/api/admin/clear-cache")
async def clear_cache():
    cache.clear()
    return {"status": "ok", "message": "Cache cleared"}


async def run_update_job(target_constituencies: Optional[List[str]], force: bool):
    start = datetime.now()
    log_update("=== UPDATE JOB STARTED ===")

    try:
        constituencies = load_constituencies()
        targets = constituencies
        if target_constituencies:
            lowered_targets = {name.lower().strip() for name in target_constituencies}
            targets = [
                item for item in constituencies
                if str(item.get("name", "")).lower().strip() in lowered_targets
            ]

        total = len(targets)
        update_status["total_constituencies"] = total
        prefer_remote = total <= int(os.getenv("HF_REMOTE_CONSTITUENCY_LIMIT", "12"))
        log_update(
            f"Processing {total} constituencies with "
            f"{'Hugging Face' if prefer_remote else 'heuristic'} sentiment mode..."
        )

        for idx, constituency in enumerate(targets):
            name = constituency.get("name", "Unknown")
            district = constituency.get("district", "Tamil Nadu")
            cache_key = f"news_{str(name).lower().strip()}"

            if not force and get_cached(cache_key):
                log_update(f"[{idx + 1}/{total}] Skipping {name} (cached)")
            else:
                try:
                    log_update(f"[{idx + 1}/{total}] Scraping {name}...")
                    result = build_news_result(name, district, prefer_remote=prefer_remote)
                    set_cache(cache_key, result)
                    bayesian.apply_news_signal(name, result)
                    log_update(
                        f"  -> Sentiment: {result['average_sentiment']:.2f} | "
                        f"Articles: {result['article_count']} | "
                        f"Signal: {result['signal_strength']:.2f}"
                    )
                    await asyncio.sleep(0.25)
                except Exception as exc:
                    log_update(f"  x Error for {name}: {exc}")

            update_status["constituencies_updated"] = idx + 1
            update_status["progress"] = round((idx + 1) / max(total, 1) * 100)

        for key in ("summary", "neck_and_neck", "surprises"):
            cache.pop(key, None)

        elapsed = (datetime.now() - start).total_seconds()
        update_status["last_run"] = datetime.now().isoformat()
        update_status["last_run_duration"] = f"{elapsed:.1f}s"
        log_update(f"=== UPDATE COMPLETE in {elapsed:.1f}s ===")
    except Exception as exc:
        log_update(f"FATAL ERROR: {exc}")
    finally:
        update_status["running"] = False


if os.path.exists(DIST_PATH):
    assets_path = os.path.join(DIST_PATH, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/tn_assembly.geojson")
    async def serve_geojson():
        geojson_path = find_file("tn_assembly.geojson")
        if not geojson_path:
            raise HTTPException(status_code=404, detail="GeoJSON not found.")
        return FileResponse(geojson_path)

    @app.get("/constituencies.json")
    async def serve_constituencies_json():
        data_path = find_file("constituencies.json")
        if not data_path:
            raise HTTPException(status_code=404, detail="Constituency data not found.")
        return FileResponse(data_path)

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(DIST_PATH, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_PATH, "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "Run 'npm run build' first to generate the dist/ folder."}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
