import json
import math
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


@dataclass
class BayesianSeatState:
    ac_no: int
    name: str
    district: str
    region: str
    prior_margin_pct: float
    logit_spa: float
    logit_nda: float
    update_count: int = 0
    last_sentiment: float = 0.0
    last_weight: float = 0.0
    last_updated: str = ""

    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()

    @staticmethod
    def sigmoid(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-max(-20, min(20, x))))

    def apply_signal(self, score: float, weight: float):
        delta = score * weight * (1.1 if self.prior_margin_pct < 5 else 0.95)
        self.logit_spa += delta
        self.logit_nda -= delta * 0.9
        self.update_count += 1
        self.last_sentiment = score
        self.last_weight = weight
        self.last_updated = datetime.now().isoformat()

    @property
    def spa_prob(self) -> float:
        return round(self.sigmoid(self.logit_spa) * 100, 1)

    @property
    def nda_prob(self) -> float:
        return round(self.sigmoid(self.logit_nda) * 100, 1)

    @property
    def confidence_interval(self) -> Tuple[float, float]:
        p = self.sigmoid(self.logit_spa)
        n = max(3, 5 + self.update_count * 2)
        se = math.sqrt(max(1e-6, p * (1 - p)) / n)
        lo = _clamp((p - 1.96 * se) * 100, 0.0, 100.0)
        hi = _clamp((p + 1.96 * se) * 100, 0.0, 100.0)
        return round(lo, 1), round(hi, 1)

    @property
    def margin_category(self) -> str:
        diff = abs(self.spa_prob - self.nda_prob)
        if diff > 12:
            return "safe"
        if diff > 4:
            return "lean"
        return "tossup"


def _to_logit(probability: float) -> float:
    probability = _clamp(probability, 0.05, 0.95)
    return math.log(probability / (1 - probability))


class BayesianPredictor:
    def __init__(self, data_path: Optional[str] = None):
        self._seats: Dict[int, BayesianSeatState] = {}
        self._name_to_ac: Dict[str, int] = {}
        self._signal_multiplier: float = 1.0
        self._load_from_dataset(data_path)

    def set_signal_multiplier(self, value: float):
        self._signal_multiplier = _clamp(float(value), 0.5, 1.5)

    def _load_from_dataset(self, data_path: Optional[str]):
        if data_path and os.path.exists(data_path):
            with open(data_path, encoding="utf-8") as handle:
                constituencies = json.load(handle)

            for item in constituencies:
                ac_no = int(item.get("acNo", 0))
                name = item.get("name", f"AC #{ac_no}")
                district = item.get("district", "Tamil Nadu")
                region = item.get("region", "STATE")
                prediction = item.get("prediction", {})
                result_2021 = item.get("result2021", {})

                total_top_two = max(
                    1,
                    int(result_2021.get("winnerVotes", 0)) + int(result_2021.get("runnerUpVotes", 0)),
                )
                margin_pct = (
                    abs(
                        int(result_2021.get("winnerVotes", 0))
                        - int(result_2021.get("runnerUpVotes", 0))
                    )
                    / total_top_two
                ) * 100

                spa_prob = float(prediction.get("spaWinProb", 52.0)) / 100
                nda_prob = float(prediction.get("ndaWinProb", 34.0)) / 100
                if spa_prob + nda_prob > 0.95:
                    scale = 0.95 / (spa_prob + nda_prob)
                    spa_prob *= scale
                    nda_prob *= scale

                seat = BayesianSeatState(
                    ac_no=ac_no,
                    name=name,
                    district=district,
                    region=region,
                    prior_margin_pct=margin_pct,
                    logit_spa=_to_logit(spa_prob),
                    logit_nda=_to_logit(nda_prob),
                )
                self._seats[ac_no] = seat
                self._register_aliases(name, district, ac_no)
            return

        for ac_no in range(1, 235):
            seat = BayesianSeatState(
                ac_no=ac_no,
                name=f"AC #{ac_no}",
                district="Tamil Nadu",
                region="STATE",
                prior_margin_pct=8.0,
                logit_spa=_to_logit(0.55),
                logit_nda=_to_logit(0.35),
            )
            self._seats[ac_no] = seat
            self._register_aliases(seat.name, seat.district, ac_no)

    def _register_aliases(self, name: str, district: str, ac_no: int):
        aliases = {
            name.lower().strip(),
            f"{name.lower().strip()} constituency",
            f"{name.lower().strip()}, {district.lower().strip()}",
        }
        for alias in aliases:
            self._name_to_ac[alias] = ac_no

    def _lookup_ac(self, constituency_name: str) -> Optional[int]:
        key = constituency_name.lower().strip()
        if key in self._name_to_ac:
            return self._name_to_ac[key]
        for alias, ac_no in self._name_to_ac.items():
            if key in alias or alias in key:
                return ac_no
        return None

    def apply_news_signal(self, constituency_name: str, signal: Dict):
        ac_no = self._lookup_ac(constituency_name)
        if not ac_no or ac_no not in self._seats:
            return

        seat = self._seats[ac_no]
        sentiment = float(signal.get("average_sentiment", 0.0))
        confidence = float(signal.get("average_confidence", 0.4))
        article_count = int(signal.get("article_count", 0))
        source_diversity = int(signal.get("source_diversity", 1))
        signal_strength = float(signal.get("signal_strength", 0.2))

        volatility = 1.15 if seat.prior_margin_pct <= 5 else 1.0 if seat.prior_margin_pct <= 12 else 0.85
        weight = (
            0.14
            + min(article_count, 8) * 0.035
            + min(source_diversity, 4) * 0.05
            + signal_strength * 0.18
            + confidence * 0.08
        ) * volatility
        seat.apply_signal(sentiment, _clamp(weight * self._signal_multiplier, 0.08, 0.95))

    def get_constituency_prediction(self, ac_no: int) -> Optional[dict]:
        seat = self._seats.get(ac_no)
        if not seat:
            return None

        lo, hi = seat.confidence_interval
        volatility = min(1.0, 0.25 + seat.update_count * 0.08 + abs(seat.last_sentiment) * 0.4)
        tvk = round(_clamp(6.5 + volatility * 4.2, 4.0, 15.0), 1)
        ntk = round(_clamp(4.0 + volatility * 2.8, 2.5, 9.0), 1)

        return {
            "ac_no": ac_no,
            "name": seat.name,
            "district": seat.district,
            "region": seat.region,
            "spa_win_prob": seat.spa_prob,
            "nda_win_prob": seat.nda_prob,
            "tvk_win_prob": tvk,
            "ntk_win_prob": ntk,
            "confidence_interval_lo": lo,
            "confidence_interval_hi": hi,
            "margin": seat.margin_category,
            "update_count": seat.update_count,
            "last_sentiment": round(seat.last_sentiment, 3),
            "last_weight": round(seat.last_weight, 3),
            "last_updated": seat.last_updated,
        }

    def get_summary(self) -> dict:
        all_preds = [self.get_constituency_prediction(ac_no) for ac_no in sorted(self._seats)]
        spa_seats = sum(1 for p in all_preds if p and p["spa_win_prob"] > p["nda_win_prob"])
        nda_seats = sum(1 for p in all_preds if p and p["nda_win_prob"] > p["spa_win_prob"])
        tossups = sum(1 for p in all_preds if p and p["margin"] == "tossup")
        lean = sum(1 for p in all_preds if p and p["margin"] == "lean")

        return {
            "total_seats": len(self._seats),
            "magic_number": 118,
            "spa_seats": spa_seats,
            "nda_seats": nda_seats,
            "tvk_seats": 0,
            "ntk_seats": 0,
            "others_seats": max(0, len(self._seats) - spa_seats - nda_seats),
            "tossups": tossups,
            "lean_seats": lean,
            "last_updated": datetime.now().isoformat(),
        }

    def get_neck_and_neck_seats(self) -> List[dict]:
        results = [self.get_constituency_prediction(ac_no) for ac_no in sorted(self._seats)]
        results = [item for item in results if item and item["margin"] == "tossup"]
        results.sort(key=lambda item: abs(item["spa_win_prob"] - item["nda_win_prob"]))
        return results[:30]

    def get_surprise_seats(self) -> List[dict]:
        results = []
        for ac_no in sorted(self._seats):
            prediction = self.get_constituency_prediction(ac_no)
            if not prediction:
                continue
            trailing = min(prediction["spa_win_prob"], prediction["nda_win_prob"])
            if 25 <= trailing <= 45:
                results.append({**prediction, "upset_probability": round(trailing, 1)})
        results.sort(key=lambda item: -item["upset_probability"])
        return results[:20]
