from dataclasses import dataclass
from typing import Literal


SourceKind = Literal["election", "news", "social", "survey", "demographic", "maps"]


@dataclass(frozen=True)
class DataSource:
    name: str
    kind: SourceKind
    priority: int
    url: str
    notes: str
    machine_readable: bool = False


TN_SOURCE_REGISTRY: list[DataSource] = [
    DataSource(
        name="Election Commission of India (ECI)",
        kind="election",
        priority=1,
        url="https://www.eci.gov.in/",
        notes="Official results archive, affidavits, candidate filings, turnout and booth data.",
        machine_readable=False,
    ),
    DataSource(
        name="Delimitation & Constituency Maps",
        kind="maps",
        priority=1,
        url="https://www.eci.gov.in/",
        notes="Boundary references used to validate and align TN constituency GeoJSON mapping.",
        machine_readable=False,
    ),
    DataSource(
        name="Lokniti / CSDS",
        kind="survey",
        priority=2,
        url="https://www.lokniti.org/",
        notes="Pre-poll and post-poll survey data for alliance and social-group level calibration.",
        machine_readable=False,
    ),
    DataSource(
        name="GDELT",
        kind="news",
        priority=2,
        url="https://www.gdeltproject.org/",
        notes="Event extraction and media intensity feed for daily issue salience tracking.",
        machine_readable=True,
    ),
    DataSource(
        name="News API",
        kind="news",
        priority=2,
        url="https://newsapi.org/",
        notes="Headline feed for NLP sentiment and narrative velocity updates.",
        machine_readable=True,
    ),
    DataSource(
        name="Google Trends",
        kind="social",
        priority=3,
        url="https://trends.google.com/",
        notes="Search-intent momentum signals for alliance and issue-level trend tracking.",
        machine_readable=False,
    ),
    DataSource(
        name="X API v2",
        kind="social",
        priority=3,
        url="https://developer.x.com/en/docs/twitter-api",
        notes="Social discourse and candidate-level narrative shifts.",
        machine_readable=True,
    ),
    DataSource(
        name="YouTube Data API",
        kind="social",
        priority=3,
        url="https://developers.google.com/youtube/v3",
        notes="High-impact political video and influencer narrative signals in Tamil media space.",
        machine_readable=True,
    ),
]


def get_candidate_sync_presets() -> dict:
    return {
        "note": "Use machine-readable feeds for automated import. Web pages marked non-machine-readable should be used for validation/citation.",
        "presets": [
            {
                "id": "tn_public_candidates_bootstrap",
                "label": "TN Public Candidate Bootstrap (GitHub CSV feeds)",
                "urls": [
                    "https://raw.githubusercontent.com/kracekumar/Tamil-Nadu-Assembly-Election-2021/master/candidates.csv",
                    "https://raw.githubusercontent.com/kracekumar/Tamil-Nadu-Assembly-Election-2021/master/tn_2021_election_candidates.csv",
                ]
            },
            {
                "id": "tn_repo_curated_candidates",
                "label": "Current Repo Curated Candidate Snapshot",
                "urls": [
                    "https://raw.githubusercontent.com/kalilurrahman/tn-election-predictor/master/tn-predictor-final/public/tn_candidates_2026.csv"
                ]
            },
            {
                "id": "tn_eci_reference_pages",
                "label": "ECI Reference Pages (HTML parse when available)",
                "urls": [
                    "https://www.eci.gov.in/",
                    "https://results.eci.gov.in/",
                ]
            }
        ],
        "election_results_presets": [
            {
                "id": "tn_historical_results_csv",
                "label": "Tamil Nadu Historical Results (CSV format required)",
                "urls": [
                    "https://raw.githubusercontent.com/kalilurrahman/tn-election-predictor/master/tn-predictor-final/public/tn_election_results_history.csv"
                ],
                "required_columns": [
                    "ac_no",
                    "constituency",
                    "year",
                    "winner",
                    "winner_party",
                    "runner_up",
                    "runner_up_party",
                    "winner_votes",
                    "runner_up_votes",
                ],
            }
        ],
        "references": [
            {
                "name": source.name,
                "kind": source.kind,
                "url": source.url,
                "machine_readable": source.machine_readable,
                "notes": source.notes,
            }
            for source in TN_SOURCE_REGISTRY
        ],
    }


def default_candidate_source_urls() -> list[str]:
    payload = get_candidate_sync_presets()
    presets = payload.get("presets", []) if isinstance(payload, dict) else []
    preferred_ids = {"tn_public_candidates_bootstrap", "tn_repo_curated_candidates"}
    urls: list[str] = []

    for preset in presets:
        if not isinstance(preset, dict):
            continue
        if str(preset.get("id", "")) not in preferred_ids:
            continue
        for raw_url in preset.get("urls", []) or []:
            url = str(raw_url).strip()
            if url and url not in urls:
                urls.append(url)

    if not urls and presets:
        first = presets[0] if isinstance(presets[0], dict) else {}
        for raw_url in first.get("urls", []) or []:
            url = str(raw_url).strip()
            if url and url not in urls:
                urls.append(url)

    return urls


def default_election_results_source_urls() -> list[str]:
    payload = get_candidate_sync_presets()
    presets = payload.get("election_results_presets", []) if isinstance(payload, dict) else []
    urls: list[str] = []

    for preset in presets:
        if not isinstance(preset, dict):
            continue
        for raw_url in preset.get("urls", []) or []:
            url = str(raw_url).strip()
            if url and url not in urls:
                urls.append(url)

    return urls
