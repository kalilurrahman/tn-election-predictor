import json
import os
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class SentimentModelOption:
    id: str
    hf_model: str
    label: str
    notes: str


@dataclass(frozen=True)
class ForecastProfileOption:
    id: str
    label: str
    signal_multiplier: float
    notes: str


SENTIMENT_OPTIONS: List[SentimentModelOption] = [
    SentimentModelOption(
        id="xlm_twitter",
        hf_model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
        label="XLM-R Twitter Sentiment",
        notes="Multilingual sentiment baseline for short political text.",
    ),
    SentimentModelOption(
        id="distilbert_sst2",
        hf_model="distilbert-base-uncased-finetuned-sst-2-english",
        label="DistilBERT SST-2",
        notes="Fast English sentiment fallback model.",
    ),
]


FORECAST_OPTIONS: List[ForecastProfileOption] = [
    ForecastProfileOption(
        id="balanced",
        label="Balanced",
        signal_multiplier=1.0,
        notes="Default update sensitivity for mixed signal environments.",
    ),
    ForecastProfileOption(
        id="conservative",
        label="Conservative",
        signal_multiplier=0.75,
        notes="Slower posterior movement, useful with sparse/noisy updates.",
    ),
    ForecastProfileOption(
        id="aggressive",
        label="Aggressive",
        signal_multiplier=1.25,
        notes="Faster posterior movement, useful with dense high-confidence updates.",
    ),
]


class ModelRegistry:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.path = os.path.join(base_dir, "data", "processed", "model_selection.json")
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def defaults(self) -> Dict:
        default_hf = os.getenv("HF_SENTIMENT_MODEL", SENTIMENT_OPTIONS[0].hf_model)
        return {
            "sentiment_model_id": SENTIMENT_OPTIONS[0].id,
            "sentiment_hf_model": default_hf,
            "forecast_profile_id": "balanced",
            "updated_at": None,
        }

    def load(self) -> Dict:
        if not os.path.exists(self.path):
            return self.defaults()
        try:
            with open(self.path, encoding="utf-8") as handle:
                stored = json.load(handle)
            merged = self.defaults()
            merged.update(stored or {})
            return merged
        except Exception:
            return self.defaults()

    def save(self, payload: Dict):
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

    def get_catalog(self) -> Dict:
        return {
            "sentiment_models": [vars(item) for item in SENTIMENT_OPTIONS],
            "forecast_profiles": [vars(item) for item in FORECAST_OPTIONS],
        }

    def get_forecast_multiplier(self, profile_id: str) -> float:
        for item in FORECAST_OPTIONS:
            if item.id == profile_id:
                return item.signal_multiplier
        return 1.0

    def get_sentiment_model(self, model_id: str) -> str:
        for item in SENTIMENT_OPTIONS:
            if item.id == model_id:
                return item.hf_model
        return SENTIMENT_OPTIONS[0].hf_model
