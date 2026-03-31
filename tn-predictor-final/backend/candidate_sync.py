import csv
import io
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests


def _normalize_name(value: str) -> str:
    cleaned = (value or "").strip().lower()
    cleaned = re.sub(r"\(.*?\)", "", cleaned)
    cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _normalize_state(value: str) -> str:
    text = (value or "").strip()
    return "Tamil Nadu" if text.lower() in {"tn", "t.n.", "tamilnadu"} else text


def _to_bool(value) -> bool:
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "y"}


def _pick(record: Dict, keys: List[str], default=None):
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return default


class CandidateSyncEngine:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.public_dir = os.path.join(base_dir, "public")
        self.dist_dir = os.path.join(base_dir, "dist")
        self.curated_filename = "constituencies_curated.json"
        self.default_filename = "constituencies.json"

    def load_master(self) -> Tuple[List[Dict], str]:
        curated = os.path.join(self.public_dir, self.curated_filename)
        fallback = os.path.join(self.public_dir, self.default_filename)
        selected = curated if os.path.exists(curated) else fallback
        with open(selected, encoding="utf-8") as handle:
            rows = json.load(handle)
        return rows, selected

    def build_geo_index(self) -> Dict[int, Dict]:
        path = os.path.join(self.public_dir, "tn_assembly.geojson")
        if not os.path.exists(path):
            return {}
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        index = {}
        for feature in data.get("features", []):
            props = feature.get("properties", {}) or {}
            ac_no = props.get("ac_no")
            if isinstance(ac_no, str) and ac_no.isdigit():
                ac_no = int(ac_no)
            if not isinstance(ac_no, int):
                continue
            if ac_no in index:
                continue
            index[ac_no] = {
                "ac_name": props.get("ac_name"),
                "pc_name": props.get("pc_name"),
                "ac_id": props.get("ac_id"),
            }
        return index

    def align_with_geojson(self, rows: List[Dict]) -> List[Dict]:
        geo_index = self.build_geo_index()
        aligned = []
        for row in rows:
            out = dict(row)
            ac_no = int(out.get("acNo", 0) or 0)
            geo = geo_index.get(ac_no)
            if geo:
                current_name = str(out.get("name", ""))
                if current_name.startswith("Constituency #") or not current_name.strip():
                    out["name"] = geo.get("ac_name") or current_name
                out.setdefault("mapName", geo.get("ac_name"))
                pc_name = str(geo.get("pc_name") or "").split("(")[0].strip().title()
                if pc_name and (not out.get("district") or str(out.get("district")).startswith("District #")):
                    out["district"] = pc_name
            aligned.append(out)
        return aligned

    def parse_candidate_payload(self, raw_text: str, content_type: str) -> List[Dict]:
        if "json" in (content_type or "").lower() or raw_text.strip().startswith("["):
            parsed = json.loads(raw_text)
            if isinstance(parsed, dict):
                if "rows" in parsed and isinstance(parsed["rows"], list):
                    parsed = parsed["rows"]
                elif "data" in parsed and isinstance(parsed["data"], list):
                    parsed = parsed["data"]
                else:
                    parsed = []
            return parsed if isinstance(parsed, list) else []

        reader = csv.DictReader(io.StringIO(raw_text))
        return [dict(row) for row in reader]

    def fetch_source(self, url: str, timeout: int = 30) -> List[Dict]:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        return self.parse_candidate_payload(response.text, content_type)

    def normalize_candidate_record(self, record: Dict) -> Dict:
        return {
            "ac_no": int(_pick(record, ["ac_no", "acNo", "constituency_no", "assembly_constituency_no"], 0) or 0),
            "constituency_name": _pick(record, ["constituency", "constituency_name", "ac_name", "seat_name"], ""),
            "district": _normalize_state(_pick(record, ["district", "pc_name", "parliamentary_constituency"], "")),
            "state": _normalize_state(_pick(record, ["state", "st_name", "state_name"], "Tamil Nadu")),
            "candidate_name": _pick(record, ["candidate_name", "name", "candidate"], ""),
            "party": _pick(record, ["party", "party_name", "abbr"], "IND"),
            "alliance": _pick(record, ["alliance", "front", "coalition"], "OTHERS"),
            "education": _pick(record, ["education", "edu"], "NA"),
            "assets": _pick(record, ["assets", "declared_assets"], "NA"),
            "liabilities": _pick(record, ["liabilities", "declared_liabilities"], "NA"),
            "cases": int(_pick(record, ["cases", "criminal_cases"], 0) or 0),
            "is_incumbent": _to_bool(_pick(record, ["is_incumbent", "incumbent"], False)),
            "literacy": float(_pick(record, ["literacy", "literacy_score"], 0) or 0),
            "age": int(_pick(record, ["age"], 0) or 0),
            "gender": _pick(record, ["gender", "sex"], "NA"),
            "profession": _pick(record, ["profession", "occupation"], "NA"),
            "community": _pick(record, ["community", "caste_group"], "NA"),
            "eci_approved": _to_bool(_pick(record, ["eci_approved", "eci_verified", "approved_by_eci"], False)),
            "party_approved": _to_bool(_pick(record, ["party_approved", "approved_by_party"], False)),
            "nomination_status": _pick(record, ["nomination_status", "status"], "unknown"),
            "nomination_date": _pick(record, ["nomination_date", "date_of_nomination"], ""),
            "affidavit_url": _pick(record, ["affidavit_url", "eci_affidavit_url", "candidate_affidavit"], ""),
            "eci_candidate_id": _pick(record, ["eci_candidate_id", "candidate_id"], ""),
            "contact": _pick(record, ["contact", "phone", "mobile"], ""),
            "website": _pick(record, ["website", "official_website"], ""),
            "x_handle": _pick(record, ["x_handle", "twitter", "twitter_handle"], ""),
            "source": _pick(record, ["source", "provider"], "external"),
        }

    def merge_candidates(self, rows: List[Dict], candidate_rows: List[Dict]) -> List[Dict]:
        ac_index = {int(r.get("acNo", 0)): i for i, r in enumerate(rows)}
        name_index = {_normalize_name(str(r.get("name", ""))): i for i, r in enumerate(rows)}
        grouped: Dict[int, List[Dict]] = {}

        for raw in candidate_rows:
            norm = self.normalize_candidate_record(raw)
            target_idx = None
            if norm["ac_no"] and norm["ac_no"] in ac_index:
                target_idx = ac_index[norm["ac_no"]]
            elif norm["constituency_name"]:
                target_idx = name_index.get(_normalize_name(norm["constituency_name"]))
            if target_idx is None:
                continue
            grouped.setdefault(target_idx, []).append(
                {
                    "name": norm["candidate_name"],
                    "party": norm["party"],
                    "alliance": norm["alliance"],
                    "isIncumbent": norm["is_incumbent"],
                    "education": norm["education"],
                    "assets": norm["assets"],
                    "liabilities": norm["liabilities"],
                    "cases": norm["cases"],
                    "literacy": norm["literacy"] if norm["literacy"] > 0 else 85.0,
                    "age": norm["age"] if norm["age"] > 0 else None,
                    "gender": norm["gender"],
                    "profession": norm["profession"],
                    "community": norm["community"],
                    "eciApproved": norm["eci_approved"],
                    "partyApproved": norm["party_approved"],
                    "nominationStatus": norm["nomination_status"],
                    "nominationDate": norm["nomination_date"],
                    "affidavitUrl": norm["affidavit_url"],
                    "eciCandidateId": norm["eci_candidate_id"],
                    "contact": norm["contact"],
                    "website": norm["website"],
                    "xHandle": norm["x_handle"],
                    "source": norm["source"],
                }
            )

        updated = []
        for idx, row in enumerate(rows):
            out = dict(row)
            if idx in grouped and grouped[idx]:
                out["candidates2026"] = grouped[idx][:8]
            updated.append(out)
        return updated

    def write_curated(self, rows: List[Dict]):
        payload = json.dumps(rows, ensure_ascii=False)
        for folder in (self.public_dir, self.dist_dir):
            target = os.path.join(folder, self.curated_filename)
            with open(target, "w", encoding="utf-8") as handle:
                handle.write(payload)

    def run_sync(self, source_urls: List[str]) -> Dict:
        rows, source_file = self.load_master()
        aligned = self.align_with_geojson(rows)

        imported = 0
        provider_stats = []
        merged_rows = aligned
        for url in source_urls:
            try:
                records = self.fetch_source(url)
                imported += len(records)
                merged_rows = self.merge_candidates(merged_rows, records)
                provider_stats.append({"url": url, "records": len(records), "status": "ok"})
            except Exception as exc:
                provider_stats.append({"url": url, "records": 0, "status": f"error: {exc}"})

        self.write_curated(merged_rows)
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source_file": source_file,
            "rows": len(merged_rows),
            "imported_records": imported,
            "providers": provider_stats,
            "output_file": os.path.join(self.public_dir, self.curated_filename),
        }
