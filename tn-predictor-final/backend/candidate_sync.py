import csv
import difflib
import io
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests
from backend.eci_adapter import parse_eci_html_candidates


def _normalize_name(value: str) -> str:
    cleaned = (value or "").strip().lower()
    cleaned = cleaned.replace("(", " ").replace(")", " ")
    cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _normalize_constituency(value: str) -> str:
    cleaned = _normalize_name(value)
    cleaned = cleaned.replace(" constituency", " ")
    cleaned = cleaned.replace(" assembly", " ")
    cleaned = re.sub(r"\bsc\b", " ", cleaned)
    cleaned = re.sub(r"\bst\b", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _constituency_aliases(value: str) -> List[str]:
    base = _normalize_constituency(value)
    aliases = {base}
    if not base:
        return []
    aliases.add(base.replace("th", "t"))
    aliases.add(base.replace("dh", "d"))
    aliases.add(base.replace("pp", "p"))
    aliases.add(base.replace("tt", "t"))
    aliases.add(base.replace("zh", "l"))
    aliases.add(base.replace("iy", "i"))
    return [alias.strip() for alias in aliases if alias.strip()]


def _normalize_state(value: str) -> str:
    text = (value or "").strip()
    return "Tamil Nadu" if text.lower() in {"tn", "t.n.", "tamilnadu"} else text


def _to_bool(value) -> bool:
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "y"}


def _to_int(value, default: int = 0) -> int:
    if value in (None, ""):
        return default
    try:
        cleaned = re.sub(r"[^0-9\-]", "", str(value))
        return int(cleaned) if cleaned else default
    except ValueError:
        return default


def _to_float(value, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    try:
        cleaned = re.sub(r"[^0-9.\-]", "", str(value))
        return float(cleaned) if cleaned else default
    except ValueError:
        return default


MANUAL_DISTRICT_OVERRIDES = {
    "thiru vi ka nagar": "Chennai",
    "chepauk thiruvalliken": "Chennai",
    "shozhinganallur": "Chennai",
    "thalli": "Krishnagiri",
    "palacodu": "Dharmapuri",
    "viluppuram": "Villupuram",
    "paramathi velur": "Namakkal",
    "colachel": "Kanyakumari",
}


def _is_placeholder_candidate_name(value: str) -> bool:
    text = _normalize_name(value)
    if not text:
        return True
    if "nominee" in text:
        return True
    if text in {"party nominee", "candidate tba", "tba", "to be announced"}:
        return True
    return False


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
        self._district_lookup = self._build_constituency_district_lookup()

    def _build_constituency_district_lookup(self) -> Dict[str, str]:
        lookup: Dict[str, str] = {}
        candidate_sources = [
            os.path.join(self.base_dir, "data", "external", "github_myneta_candidates.csv"),
            os.path.join(self.public_dir, "tn_candidates_2026.csv"),
        ]
        for source in candidate_sources:
            if not os.path.exists(source):
                continue
            try:
                with open(source, encoding="utf-8") as handle:
                    reader = csv.DictReader(handle)
                    for row in reader:
                        constituency = (
                            row.get("Constituency")
                            or row.get("constituency")
                            or row.get("ac_name")
                            or row.get("ac_name")
                            or ""
                        ).strip()
                        district = (
                            row.get("District")
                            or row.get("district")
                            or row.get("district_name")
                            or ""
                        ).strip()
                        if not constituency or not district:
                            continue
                        key = _normalize_constituency(constituency)
                        if key and key not in lookup:
                            lookup[key] = district
            except Exception:
                continue
        return lookup

    def _lookup_district(self, constituency_name: str) -> Optional[str]:
        if not constituency_name:
            return None
        key = _normalize_constituency(constituency_name)
        if key in MANUAL_DISTRICT_OVERRIDES:
            return MANUAL_DISTRICT_OVERRIDES[key]
        if key in self._district_lookup:
            return self._district_lookup[key]

        for candidate_key, district in self._district_lookup.items():
            if (key.startswith(candidate_key) or candidate_key.startswith(key)) and abs(len(candidate_key) - len(key)) <= 5:
                return district

        best_key = None
        best_score = 0.0
        key_tokens = set(key.split())
        best_overlap = 0
        for candidate_key in self._district_lookup.keys():
            score = difflib.SequenceMatcher(a=key, b=candidate_key).ratio()
            overlap = len(key_tokens.intersection(set(candidate_key.split())))
            if score > best_score and overlap >= 1:
                best_key = candidate_key
                best_score = score
                best_overlap = overlap
            elif score > best_score and len(key_tokens) == 1:
                best_key = candidate_key
                best_score = score
                best_overlap = overlap
        if best_key and (best_score >= 0.9 and best_overlap >= 1 or best_score >= 0.94):
            return self._district_lookup[best_key]
        return None

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
                geo_name = str(geo.get("ac_name") or "").strip()
                if geo_name:
                    if current_name.startswith("Constituency #") or not current_name.strip() or _normalize_constituency(current_name) != _normalize_constituency(geo_name):
                        out["name"] = geo_name
                    out["mapName"] = geo_name
                pc_name = str(geo.get("pc_name") or "").split("(")[0].strip().title()
                mapped_district = self._lookup_district(str(out.get("name", ""))) or self._lookup_district(current_name)
                if mapped_district:
                    out["district"] = mapped_district
                elif pc_name and (not out.get("district") or str(out.get("district")).startswith("District #") or str(out.get("district")).strip().lower() in {"tn", "tamil nadu", "state"}):
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
        payload = self.parse_candidate_payload(response.text, content_type)
        if payload:
            return payload

        # Fallback for ECI-like HTML pages with candidate tables
        if "eci.gov.in" in url.lower() or "eci" in url.lower():
            html_rows = parse_eci_html_candidates(response.text, source_url=url)
            if html_rows:
                return html_rows

        return []

    def normalize_candidate_record(self, record: Dict) -> Dict:
        normalized = {}
        for key, value in record.items():
            normalized[str(key).strip().lower().replace(" ", "_")] = value

        def pick(keys: List[str], default=None):
            for key in keys:
                value = normalized.get(key)
                if value not in (None, ""):
                    return value
            return default

        return {
            "ac_no": _to_int(pick(["ac_no", "acno", "constituency_no", "assembly_constituency_no", "constituency_id"], 0), 0),
            "constituency_name": pick(["constituency", "constituency_name", "ac_name", "seat_name"], ""),
            "district": _normalize_state(str(pick(["district", "pc_name", "parliamentary_constituency"], ""))),
            "state": _normalize_state(str(pick(["state", "st_name", "state_name"], "Tamil Nadu"))),
            "candidate_name": pick(["candidate_name", "name", "candidate"], ""),
            "party": pick(["party", "party_name", "abbr"], "IND"),
            "alliance": pick(["alliance", "front", "coalition"], "OTHERS"),
            "education": pick(["education", "edu"], "NA"),
            "assets": pick(["assets", "declared_assets", "total_assets"], "NA"),
            "liabilities": pick(["liabilities", "declared_liabilities"], "NA"),
            "cases": _to_int(pick(["cases", "criminal_cases", "criminal_cases"], 0), 0),
            "is_incumbent": _to_bool(pick(["is_incumbent", "incumbent"], False)),
            "literacy": _to_float(pick(["literacy", "literacy_score"], 0), 0),
            "age": _to_int(pick(["age"], 0), 0),
            "gender": pick(["gender", "sex"], "NA"),
            "profession": pick(["profession", "occupation"], "NA"),
            "community": pick(["community", "caste_group"], "NA"),
            "eci_approved": _to_bool(pick(["eci_approved", "eci_verified", "approved_by_eci"], False)),
            "party_approved": _to_bool(pick(["party_approved", "approved_by_party"], False)),
            "nomination_status": pick(["nomination_status", "status"], "unknown"),
            "nomination_date": pick(["nomination_date", "date_of_nomination"], ""),
            "affidavit_url": pick(["affidavit_url", "eci_affidavit_url", "candidate_affidavit"], ""),
            "eci_candidate_id": pick(["eci_candidate_id", "candidate_id", "pk"], ""),
            "contact": pick(["contact", "phone", "mobile"], ""),
            "website": pick(["website", "official_website"], ""),
            "x_handle": pick(["x_handle", "twitter", "twitter_handle"], ""),
            "is_rerunner": _to_bool(pick(["is_rerunner", "rerunner"], False)),
            "is_celebrity": _to_bool(pick(["is_celebrity", "celebrity"], False)),
            "validation_reports": pick(["validation_reports", "report_links", "source_links"], []),
            "source": pick(["source", "provider"], "external"),
        }

    def _candidate_key(self, candidate: Dict) -> str:
        party_key = _normalize_name(str(candidate.get("party", "")))
        if party_key:
            return f"party:{party_key}"
        name_key = _normalize_name(str(candidate.get("name", "")))
        if name_key:
            return f"name:{name_key}"
        return "unknown"

    def _candidate_score(self, candidate: Dict) -> int:
        name = str(candidate.get("name", "")).strip()
        party = str(candidate.get("party", "")).strip().upper()
        nomination_status = str(candidate.get("nominationStatus", "")).strip().lower()
        source = str(candidate.get("source", "")).strip().lower()

        score = 0
        if _is_placeholder_candidate_name(name):
            score -= 120
        else:
            score += 120

        if party and party not in {"IND", "INDEPENDENT"}:
            score += 20
        if candidate.get("eciApproved"):
            score += 25
        if candidate.get("partyApproved"):
            score += 15
        if candidate.get("affidavitUrl"):
            score += 10
        if nomination_status in {"accepted", "confirmed", "valid", "filed"}:
            score += 12
        if source in {"eci", "eci_html", "github_myneta", "myneta", "adr"}:
            score += 10
        if source == "generated":
            score -= 30
        return score

    def _merge_candidate_lists(self, existing: List[Dict], incoming: List[Dict], limit: int = 8) -> List[Dict]:
        best: Dict[str, Tuple[int, int, Dict]] = {}
        order = 0

        for candidate in (existing or []) + (incoming or []):
            if not isinstance(candidate, dict):
                continue
            key = self._candidate_key(candidate)
            score = self._candidate_score(candidate)
            previous = best.get(key)
            if previous is None or score > previous[0]:
                best[key] = (score, order, candidate)
            order += 1

        ranked = sorted(best.values(), key=lambda item: (-item[0], item[1]))
        merged = [item[2] for item in ranked]

        # Prefer informative records; only keep placeholders if there are not enough real names.
        real = [row for row in merged if not _is_placeholder_candidate_name(str(row.get("name", "")))]
        placeholders = [row for row in merged if _is_placeholder_candidate_name(str(row.get("name", "")))]
        final_rows = (real + placeholders)[:limit]
        return final_rows

    def merge_candidates(self, rows: List[Dict], candidate_rows: List[Dict]) -> List[Dict]:
        ac_index = {int(r.get("acNo", 0)): i for i, r in enumerate(rows)}
        name_index: Dict[str, int] = {}
        canonical_names: List[str] = []
        for i, row in enumerate(rows):
            canonical = _normalize_constituency(str(row.get("name", "")))
            canonical_names.append(canonical)
            for alias in _constituency_aliases(str(row.get("name", ""))):
                name_index.setdefault(alias, i)
        grouped: Dict[int, Dict] = {}

        for raw in candidate_rows:
            norm = self.normalize_candidate_record(raw)
            target_idx = None
            if norm["ac_no"] and norm["ac_no"] in ac_index:
                target_idx = ac_index[norm["ac_no"]]
            elif norm["constituency_name"]:
                constituency_key = _normalize_constituency(norm["constituency_name"])
                target_idx = name_index.get(constituency_key)
                if target_idx is None:
                    for alias in _constituency_aliases(norm["constituency_name"]):
                        if alias in name_index:
                            target_idx = name_index[alias]
                            break
                if target_idx is None and canonical_names:
                    best = difflib.get_close_matches(constituency_key, canonical_names, n=1, cutoff=0.88)
                    if best:
                        target_idx = name_index.get(best[0])
            if target_idx is None:
                continue
            bucket = grouped.setdefault(target_idx, {"candidates": [], "district_counts": {}})
            bucket["candidates"].append(
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
                    "isRerunner": norm["is_rerunner"],
                    "isCelebrity": norm["is_celebrity"],
                    "validationReports": norm["validation_reports"] if isinstance(norm["validation_reports"], list) else [],
                    "source": norm["source"],
                }
            )
            district_name = str(norm.get("district", "")).strip()
            if district_name and district_name.lower() not in {"tamil nadu", "tn", "state"}:
                counts = bucket["district_counts"]
                counts[district_name] = counts.get(district_name, 0) + 1

        updated = []
        for idx, row in enumerate(rows):
            out = dict(row)
            if idx in grouped and grouped[idx]["candidates"]:
                existing_candidates = out.get("candidates2026") if isinstance(out.get("candidates2026"), list) else []
                out["candidates2026"] = self._merge_candidate_lists(
                    existing_candidates,
                    grouped[idx]["candidates"],
                    limit=8,
                )
                district_counts = grouped[idx].get("district_counts", {})
                if district_counts:
                    resolved_district = max(district_counts.items(), key=lambda item: item[1])[0]
                    out["district"] = resolved_district
            updated.append(out)
        return updated

    def write_curated(self, rows: List[Dict]) -> Dict[str, List[str]]:
        payload = json.dumps(rows, ensure_ascii=False)
        written_files: List[str] = []
        write_warnings: List[str] = []
        for folder in (self.public_dir, self.dist_dir):
            target = os.path.join(folder, self.curated_filename)
            try:
                os.makedirs(folder, exist_ok=True)
                with open(target, "w", encoding="utf-8") as handle:
                    handle.write(payload)
                written_files.append(target)
            except Exception as exc:
                write_warnings.append(f"{target}: {exc}")

        if not written_files:
            raise RuntimeError("Unable to write curated constituency data to public/dist targets.")

        return {"written_files": written_files, "write_warnings": write_warnings}

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

        write_result = self.write_curated(merged_rows)
        primary_output = write_result["written_files"][0]
        seats_with_any = 0
        seats_with_real = 0
        seats_placeholder_only = 0
        for row in merged_rows:
            candidates = row.get("candidates2026") if isinstance(row.get("candidates2026"), list) else []
            if not candidates:
                continue
            seats_with_any += 1
            has_real = any(
                not _is_placeholder_candidate_name(str((candidate or {}).get("name", "")))
                for candidate in candidates
                if isinstance(candidate, dict)
            )
            if has_real:
                seats_with_real += 1
            else:
                seats_placeholder_only += 1

        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source_file": source_file,
            "rows": len(merged_rows),
            "imported_records": imported,
            "coverage": {
                "seats_with_any_candidates": seats_with_any,
                "seats_with_real_names": seats_with_real,
                "seats_placeholder_only": seats_placeholder_only,
            },
            "providers": provider_stats,
            "output_file": primary_output,
            "output_files": write_result["written_files"],
            "write_warnings": write_result["write_warnings"],
        }
