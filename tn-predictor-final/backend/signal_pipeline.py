import os
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional

import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


@dataclass
class SentimentResult:
    score: float
    confidence: float
    label: str
    source: str
    model: str


class HuggingFaceSentimentClient:
    def __init__(self):
        self.model = os.getenv(
            "HF_SENTIMENT_MODEL",
            "cardiffnlp/twitter-xlm-roberta-base-sentiment",
        )
        self.token = os.getenv("HF_TOKEN")
        self.timeout = float(os.getenv("HF_INFERENCE_TIMEOUT", "20"))
        self.enabled = os.getenv("HF_ENABLE_REMOTE_SENTIMENT", "true").lower() != "false"
        self.endpoint = f"https://api-inference.huggingface.co/models/{self.model}"

    def classify(self, text: str) -> Optional[SentimentResult]:
        if not self.enabled or not text:
            return None

        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json={"inputs": text, "options": {"wait_for_model": True, "use_cache": True}},
                timeout=self.timeout,
            )
            response.raise_for_status()
            parsed = self._parse_response(response.json())
            if not parsed:
                return None
            score, confidence, label = parsed
            return SentimentResult(
                score=score,
                confidence=confidence,
                label=label,
                source="huggingface",
                model=self.model,
            )
        except Exception:
            return None

    def _parse_response(self, payload) -> Optional[tuple]:
        if isinstance(payload, list) and payload and isinstance(payload[0], list):
            payload = payload[0]
        if not isinstance(payload, list) or not payload:
            return None

        best = max(payload, key=lambda item: float(item.get("score", 0.0)))
        raw_label = str(best.get("label", "")).upper()
        confidence = max(0.0, min(1.0, float(best.get("score", 0.0))))

        if "NEG" in raw_label:
            return -confidence, confidence, "NEGATIVE"
        if "POS" in raw_label:
            return confidence, confidence, "POSITIVE"
        return 0.0, confidence, "NEUTRAL"


class SentimentEngine:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.remote_client = HuggingFaceSentimentClient()
        self.tamil_lexicon = {
            "வெற்றி": 0.8,
            "சிறப்பு": 0.5,
            "வளர்ச்சி": 0.6,
            "ஆதரவு": 0.4,
            "நன்மை": 0.5,
            "மகிழ்ச்சி": 0.7,
            "முன்னேற்றம்": 0.6,
            "தோல்வி": -0.8,
            "ஊழல்": -0.7,
            "எதிர்ப்பு": -0.5,
            "குற்றம்": -0.6,
            "மோசம்": -0.5,
            "பின்னடைவு": -0.6,
            "ஏமாற்றம்": -0.7,
        }

    def analyze_text(self, text: str, prefer_remote: bool = True) -> SentimentResult:
        if not text:
            return SentimentResult(0.0, 0.0, "NEUTRAL", "empty", "none")

        if prefer_remote:
            remote = self.remote_client.classify(text)
            if remote:
                return remote

        vader_score = self.analyzer.polarity_scores(text)["compound"]
        tamil_score = 0.0
        tamil_hits = 0

        for term, value in self.tamil_lexicon.items():
            if term in text:
                tamil_score += value
                tamil_hits += 1

        if tamil_hits:
            tamil_score /= tamil_hits
            combined = (vader_score * 0.6) + (tamil_score * 0.4)
            confidence = min(1.0, 0.45 + (0.1 * tamil_hits) + abs(combined) * 0.2)
        else:
            combined = vader_score
            confidence = min(1.0, 0.35 + abs(combined) * 0.35)

        return SentimentResult(
            score=combined,
            confidence=confidence,
            label=self.get_sentiment_label(combined),
            source="heuristic",
            model="vader+tamil-lexicon",
        )

    def analyze_news(
        self,
        news_items: List[Dict],
        constituency_name: str,
        district_name: str,
        issues: Optional[List[str]] = None,
        candidates: Optional[List[str]] = None,
        prefer_remote: bool = True,
    ) -> Dict:
        processed: List[Dict] = []
        weighted_total = 0.0
        total_weight = 0.0
        confidence_total = 0.0
        sources = set()
        recency_total = 0.0

        issues = issues or []
        candidates = candidates or []

        for item in news_items:
            result = self.analyze_text(item.get("title", ""), prefer_remote=prefer_remote)
            recency_weight, hours_old = self._compute_recency_weight(item.get("published"))
            relevance_weight = self._compute_relevance_weight(
                item.get("title", ""),
                constituency_name,
                district_name,
                issues,
                candidates,
            )
            article_weight = recency_weight * relevance_weight

            processed_item = {
                **item,
                "sentiment_score": round(result.score, 3),
                "sentiment_label": result.label,
                "sentiment_confidence": round(result.confidence, 3),
                "sentiment_source": result.source,
                "sentiment_model": result.model,
                "relevance_weight": round(relevance_weight, 3),
                "recency_weight": round(recency_weight, 3),
                "hours_old": None if hours_old is None else round(hours_old, 1),
            }
            processed.append(processed_item)

            weighted_total += result.score * article_weight
            total_weight += article_weight
            confidence_total += result.confidence
            if item.get("source"):
                sources.add(item["source"])
            if hours_old is not None:
                recency_total += hours_old

        average_sentiment = weighted_total / total_weight if total_weight else 0.0
        average_confidence = confidence_total / len(processed) if processed else 0.0
        source_diversity = len(sources)
        average_hours_old = recency_total / len(processed) if processed else None
        signal_strength = min(
            1.0,
            abs(average_sentiment) * 0.45
            + min(len(processed), 8) * 0.05
            + min(source_diversity, 4) * 0.08
            + average_confidence * 0.2,
        )

        return {
            "news": processed,
            "average_sentiment": round(average_sentiment, 3),
            "overall_label": self.get_sentiment_label(average_sentiment),
            "average_confidence": round(average_confidence, 3),
            "article_count": len(processed),
            "source_diversity": source_diversity,
            "average_hours_old": None if average_hours_old is None else round(average_hours_old, 2),
            "signal_strength": round(signal_strength, 3),
            "sentiment_backend": processed[0]["sentiment_source"] if processed else "none",
            "sentiment_model": processed[0]["sentiment_model"] if processed else "none",
        }

    def get_sentiment_label(self, score: float) -> str:
        if score >= 0.1:
            return "POSITIVE"
        if score <= -0.1:
            return "NEGATIVE"
        return "NEUTRAL"

    def _compute_relevance_weight(
        self,
        text: str,
        constituency_name: str,
        district_name: str,
        issues: List[str],
        candidates: List[str],
    ) -> float:
        lowered = text.lower()
        weight = 1.0

        if constituency_name.lower() in lowered:
            weight += 0.3
        if district_name.lower() in lowered:
            weight += 0.15

        for issue in issues[:3]:
            if issue.lower() in lowered:
                weight += 0.08

        for candidate in candidates[:4]:
            name_bits = [part for part in candidate.lower().split() if len(part) > 2]
            if any(bit in lowered for bit in name_bits):
                weight += 0.06

        return min(1.8, weight)

    def _compute_recency_weight(self, published: Optional[str]) -> tuple:
        if not published:
            return 1.0, None

        try:
            dt = parsedate_to_datetime(published)
        except (TypeError, ValueError):
            try:
                dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            except ValueError:
                return 1.0, None

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        hours_old = max(
            0.0,
            (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds() / 3600,
        )

        if hours_old <= 24:
            return 1.3, hours_old
        if hours_old <= 72:
            return 1.1, hours_old
        if hours_old <= 168:
            return 0.95, hours_old
        return 0.8, hours_old
