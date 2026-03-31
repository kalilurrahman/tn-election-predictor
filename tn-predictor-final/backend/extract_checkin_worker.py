import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from backend.candidate_sync import CandidateSyncEngine
from backend.election_results_sync import ElectionResultsSyncEngine


def _split_urls(value: str) -> List[str]:
    return [x.strip() for x in (value or "").split(",") if x.strip()]


class ExtractCheckinWorker:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.candidate_engine = CandidateSyncEngine(base_dir)
        self.results_engine = ElectionResultsSyncEngine(base_dir)
        self.checkin_dir = Path(base_dir) / "data" / "processed"
        self.checkin_dir.mkdir(parents=True, exist_ok=True)
        self.latest_file = self.checkin_dir / "latest_extract_checkin.json"
        self.history_file = self.checkin_dir / "extract_checkin_history.jsonl"

    def run_once(self) -> Dict:
        candidate_urls = _split_urls(os.getenv("CANDIDATE_SOURCE_URLS", ""))
        results_urls = _split_urls(os.getenv("ELECTION_RESULTS_SOURCE_URLS", ""))

        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "ok",
            "candidate_sync": None,
            "election_results_sync": None,
            "admin_checkin_required": True,
            "notes": [],
        }

        if candidate_urls:
            try:
                payload["candidate_sync"] = self.candidate_engine.run_sync(candidate_urls)
            except Exception as exc:
                payload["candidate_sync"] = {"status": "error", "error": str(exc)}
                payload["status"] = "partial"
                payload["notes"].append("Candidate sync failed; admin should verify source availability.")
        else:
            payload["notes"].append("CANDIDATE_SOURCE_URLS not configured.")

        if results_urls:
            try:
                payload["election_results_sync"] = self.results_engine.run_sync(results_urls)
            except Exception as exc:
                payload["election_results_sync"] = {"status": "error", "error": str(exc)}
                payload["status"] = "partial"
                payload["notes"].append("Election-result sync failed; admin should verify source availability.")
        else:
            payload["notes"].append("ELECTION_RESULTS_SOURCE_URLS not configured.")

        self.latest_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        with self.history_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return payload

    def run_forever(self, interval_minutes: int = 180):
        seconds = max(300, int(interval_minutes) * 60)
        while True:
            try:
                self.run_once()
            except Exception as exc:
                err = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "status": "error",
                    "admin_checkin_required": True,
                    "notes": [f"Worker exception: {exc}"],
                }
                self.latest_file.write_text(json.dumps(err, ensure_ascii=False, indent=2), encoding="utf-8")
                with self.history_file.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(err, ensure_ascii=False) + "\n")
            time.sleep(seconds)


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    worker = ExtractCheckinWorker(str(root))
    mode = os.getenv("EXTRACT_WORKER_MODE", "once").strip().lower()
    interval = int(os.getenv("EXTRACT_INTERVAL_MINUTES", "180"))
    if mode == "daemon":
        worker.run_forever(interval_minutes=interval)
    else:
        result = worker.run_once()
        print(json.dumps(result, ensure_ascii=False, indent=2))
