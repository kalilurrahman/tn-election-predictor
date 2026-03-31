import csv
import io
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List

import requests


@dataclass(frozen=True)
class DatasetSource:
    dataset_id: str
    name: str
    priority: int
    url: str
    format: str
    requires_auth: bool
    notes: str


TN_DATASET_CATALOG: List[DatasetSource] = [
    DatasetSource(
        dataset_id="dataful_tn_1967_2021",
        name="Dataful TN Assembly Results 1967-2021",
        priority=1,
        url="https://dataful.in/datasets/14452/",
        format="csv/xlsx/parquet",
        requires_auth=True,
        notes="Primary historical candidate-level dataset from ECI compilation.",
    ),
    DatasetSource(
        dataset_id="kaggle_tn_legislative_1971_2021",
        name="Kaggle TN Legislative Dataset 1971-2021",
        priority=1,
        url="https://www.kaggle.com/datasets/srinrealyf/1971-2021-tamilnadu-legislative-election-dataset",
        format="csv",
        requires_auth=True,
        notes="Cross-validation dataset; requires Kaggle auth/API.",
    ),
    DatasetSource(
        dataset_id="github_myneta_candidates",
        name="GitHub TN 2021 candidates.csv",
        priority=1,
        url="https://raw.githubusercontent.com/kracekumar/Tamil-Nadu-Assembly-Election-2021/master/candidates.csv",
        format="csv",
        requires_auth=False,
        notes="Public CSV with candidate details and declared wealth metadata.",
    ),
    DatasetSource(
        dataset_id="github_myneta_votes",
        name="GitHub TN 2021 candidate votes CSV",
        priority=1,
        url="https://raw.githubusercontent.com/kracekumar/Tamil-Nadu-Assembly-Election-2021/master/tn_2021_election_candidates.csv",
        format="csv",
        requires_auth=False,
        notes="Public CSV with candidate-level EVM/postal/total votes and vote percentages.",
    ),
    DatasetSource(
        dataset_id="eci_official_portal",
        name="Election Commission of India",
        priority=1,
        url="https://results.eci.gov.in/",
        format="html",
        requires_auth=False,
        notes="Official portal. Live scraping can be blocked; use exported files where possible.",
    ),
]


class DatasetBootstrapEngine:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.external_dir = os.path.join(base_dir, "data", "external")
        self.processed_dir = os.path.join(base_dir, "data", "processed")
        os.makedirs(self.external_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)

    def catalog(self) -> Dict:
        return {"generated_at": datetime.utcnow().isoformat() + "Z", "datasets": [asdict(x) for x in TN_DATASET_CATALOG]}

    def _download_csv(self, src: DatasetSource) -> Dict:
        response = requests.get(src.url, timeout=60)
        response.raise_for_status()
        text = response.text
        rows = list(csv.DictReader(io.StringIO(text)))
        out_path = os.path.join(self.external_dir, f"{src.dataset_id}.csv")
        with open(out_path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        return {
            "dataset_id": src.dataset_id,
            "name": src.name,
            "status": "downloaded",
            "rows": len(rows),
            "columns": list(rows[0].keys()) if rows else [],
            "path": out_path,
            "url": src.url,
        }

    def _build_candidate_feature_table(self) -> Dict:
        candidates_path = os.path.join(self.external_dir, "github_myneta_candidates.csv")
        votes_path = os.path.join(self.external_dir, "github_myneta_votes.csv")
        if not os.path.exists(candidates_path) or not os.path.exists(votes_path):
            return {"status": "skipped", "reason": "source CSVs missing"}

        with open(candidates_path, encoding="utf-8") as handle:
            candidates = list(csv.DictReader(handle))
        with open(votes_path, encoding="utf-8") as handle:
            votes = list(csv.DictReader(handle))

        idx = {}
        for row in candidates:
            key = (str(row.get("name", "")).strip().lower(), str(row.get("district", "")).strip().lower())
            idx[key] = row

        output_rows = []
        for row in votes:
            name = str(row.get("name", row.get("candidate_name", ""))).strip().lower()
            district = str(row.get("district", "")).strip().lower()
            extra = idx.get((name, district), {})
            output_rows.append(
                {
                    "candidate_name": row.get("name", row.get("candidate_name", "")),
                    "district": row.get("district", ""),
                    "constituency": row.get("constituency", row.get("cons_name", "")),
                    "party": row.get("party", ""),
                    "votes_total": row.get("total_votes", row.get("total", row.get("total_votes_secured", ""))),
                    "vote_share_pct": row.get("vote_percentage", row.get("vote_share_percentage", "")),
                    "position": row.get("position", ""),
                    "gender": row.get("gender", extra.get("gender", "")),
                    "age": extra.get("age", ""),
                    "assets": extra.get("assets", extra.get("asset", "")),
                    "liabilities": extra.get("liabilities", ""),
                    "criminal_cases": extra.get("criminal_cases", extra.get("cases", "")),
                }
            )

        out_path = os.path.join(self.processed_dir, "tn_2021_candidate_feature_table.csv")
        with open(out_path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(output_rows[0].keys()) if output_rows else [])
            if output_rows:
                writer.writeheader()
                writer.writerows(output_rows)
        return {"status": "ok", "rows": len(output_rows), "path": out_path}

    def bootstrap(self) -> Dict:
        report = []
        for src in TN_DATASET_CATALOG:
            if src.requires_auth:
                report.append(
                    {
                        "dataset_id": src.dataset_id,
                        "name": src.name,
                        "status": "manual_auth_required",
                        "url": src.url,
                        "notes": src.notes,
                    }
                )
                continue
            if src.format != "csv":
                report.append(
                    {
                        "dataset_id": src.dataset_id,
                        "name": src.name,
                        "status": "manual_or_custom_parser_required",
                        "url": src.url,
                        "notes": src.notes,
                    }
                )
                continue
            try:
                report.append(self._download_csv(src))
            except Exception as exc:
                report.append(
                    {
                        "dataset_id": src.dataset_id,
                        "name": src.name,
                        "status": f"error: {exc}",
                        "url": src.url,
                    }
                )

        feature_table = self._build_candidate_feature_table()
        summary = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "report": report,
            "feature_table": feature_table,
        }
        with open(os.path.join(self.processed_dir, "tn_dataset_bootstrap_report.json"), "w", encoding="utf-8") as handle:
            json.dump(summary, handle, ensure_ascii=False, indent=2)
        return summary
