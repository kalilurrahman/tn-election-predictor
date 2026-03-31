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
                "id": "tn_curated_bootstrap",
                "label": "TN Curated Bootstrap (CSV/JSON feeds)",
                "urls": [
                    "https://raw.githubusercontent.com/kalilurrahman/tn-election-predictor/master/tn-predictor-final/public/tn_candidates_2026.csv"
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
