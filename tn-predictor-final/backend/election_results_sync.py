import csv
import io
import json
import os
from datetime import datetime
from typing import Dict, List

import requests


class ElectionResultsSyncEngine:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.public_dir = os.path.join(base_dir, "public")
        self.dist_dir = os.path.join(base_dir, "dist")
        self.output_csv = "tn_election_results_history.csv"
        self.output_json = "tn_election_results_history.json"

    def _parse_rows(self, content: str, content_type: str) -> List[Dict]:
        if "json" in (content_type or "").lower():
            data = json.loads(content)
            rows = data.get("rows", data) if isinstance(data, dict) else data
            return rows if isinstance(rows, list) else []
        reader = csv.DictReader(io.StringIO(content))
        return [dict(row) for row in reader]

    def fetch_rows(self, url: str) -> List[Dict]:
        response = requests.get(url, timeout=45)
        response.raise_for_status()
        return self._parse_rows(response.text, response.headers.get("content-type", ""))

    def normalize_row(self, row: Dict) -> Dict:
        winner_votes = float(row.get("winner_votes", row.get("winnerVotes", 0)) or 0)
        runner_votes = float(row.get("runner_up_votes", row.get("runnerUpVotes", 0)) or 0)
        total = winner_votes + runner_votes
        margin_pct = round(((winner_votes - runner_votes) / total) * 100, 2) if total > 0 else 0.0
        return {
            "ac_no": int(row.get("ac_no", row.get("acNo", 0)) or 0),
            "constituency": row.get("constituency", row.get("ac_name", "")),
            "year": int(row.get("year", 0) or 0),
            "winner": row.get("winner", row.get("winner_name", "")),
            "winner_party": row.get("winner_party", row.get("winnerParty", "")),
            "runner_up": row.get("runner_up", row.get("runnerUp", "")),
            "runner_up_party": row.get("runner_up_party", row.get("runnerUpParty", "")),
            "winner_votes": int(winner_votes),
            "runner_up_votes": int(runner_votes),
            "margin_pct": margin_pct,
            "source_url": row.get("source_url", ""),
        }

    def _write(self, rows: List[Dict]) -> Dict[str, List[str]]:
        headers = [
            "ac_no",
            "constituency",
            "year",
            "winner",
            "winner_party",
            "runner_up",
            "runner_up_party",
            "winner_votes",
            "runner_up_votes",
            "margin_pct",
            "source_url",
        ]
        written_files: List[str] = []
        write_warnings: List[str] = []
        for folder in (self.public_dir, self.dist_dir):
            csv_path = os.path.join(folder, self.output_csv)
            json_path = os.path.join(folder, self.output_json)
            try:
                os.makedirs(folder, exist_ok=True)
                with open(csv_path, "w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=headers)
                    writer.writeheader()
                    for row in rows:
                        writer.writerow({key: row.get(key, "") for key in headers})
                with open(json_path, "w", encoding="utf-8") as handle:
                    json.dump({"rows": rows}, handle, ensure_ascii=False)
                written_files.extend([csv_path, json_path])
            except Exception as exc:
                write_warnings.append(f"{folder}: {exc}")

        if not written_files:
            raise RuntimeError("Unable to write election results artifacts to public/dist targets.")

        return {"written_files": written_files, "write_warnings": write_warnings}

    def run_sync(self, source_urls: List[str]) -> Dict:
        aggregated: List[Dict] = []
        providers = []
        for url in source_urls:
            try:
                fetched = self.fetch_rows(url)
                normalized = []
                for row in fetched:
                    item = self.normalize_row(row)
                    if item["ac_no"] <= 0 or item["year"] <= 0:
                        continue
                    item["source_url"] = url
                    normalized.append(item)
                aggregated.extend(normalized)
                providers.append({"url": url, "rows": len(normalized), "status": "ok"})
            except Exception as exc:
                providers.append({"url": url, "rows": 0, "status": f"error: {exc}"})

        unique = {(r["ac_no"], r["year"]): r for r in aggregated}
        merged = sorted(unique.values(), key=lambda x: (x["year"], x["ac_no"]))
        write_result = self._write(merged)
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "rows": len(merged),
            "providers": providers,
            "output_csv": next((path for path in write_result["written_files"] if path.endswith(".csv")), ""),
            "output_json": next((path for path in write_result["written_files"] if path.endswith(".json")), ""),
            "output_files": write_result["written_files"],
            "write_warnings": write_result["write_warnings"],
        }
