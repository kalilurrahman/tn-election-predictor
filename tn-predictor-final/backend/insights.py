import re
from typing import Dict, List, Optional


def _normalize_name(value: str) -> str:
    lowered = (value or "").strip().lower()
    lowered = re.sub(r"\(.*?\)", "", lowered)
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _safe_num(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _renormalize(probabilities: Dict[str, float]) -> Dict[str, float]:
    clipped = {k: max(0.1, v) for k, v in probabilities.items()}
    total = sum(clipped.values()) or 1.0
    return {k: round(v / total * 100, 2) for k, v in clipped.items()}


class ConstituencyInsightsEngine:
    def __init__(self):
        self.scenario_presets = {
            "baseline": {"spa": 0.0, "nda": 0.0, "tvk": 0.0, "ntk": 0.0},
            "anti_incumbency": {"spa": -2.0, "nda": 2.5, "tvk": 1.0, "ntk": 0.5},
            "youth_surge": {"spa": -2.5, "nda": -2.0, "tvk": 4.5, "ntk": 1.5},
            "leadership_wave_spa": {"spa": 4.0, "nda": -2.0, "tvk": -1.0, "ntk": -0.5},
            "fragmented_mandate": {"spa": -2.0, "nda": -2.0, "tvk": 3.5, "ntk": 2.5},
            "welfare_surge_spa": {"spa": 3.0, "nda": -1.5, "tvk": -0.5, "ntk": -0.5},
            "localized_anti_incumbency": {"spa": -3.0, "nda": 1.8, "tvk": 0.8, "ntk": 0.4},
        }

    def _margin_pct_2021(self, constituency: Dict) -> float:
        result = constituency.get("result2021", {}) or {}
        winner_votes = _safe_num(result.get("winnerVotes"))
        runner_votes = _safe_num(result.get("runnerUpVotes"))
        total = winner_votes + runner_votes
        if total <= 0:
            return 0.0
        return abs(winner_votes - runner_votes) / total * 100

    def _feature_snapshot(self, constituency: Dict) -> Dict:
        prediction = constituency.get("prediction", {}) or {}
        candidates = constituency.get("candidates2026", []) or []
        registered = _safe_num(constituency.get("registeredVoters2021"), 0.0)
        issues = len(constituency.get("keyIssues", []) or [])
        incumbents = sum(1 for c in candidates if bool(c.get("isIncumbent")))
        margin_pct = self._margin_pct_2021(constituency)
        turnout = _safe_num((constituency.get("result2021", {}) or {}).get("turnoutPercent"), 70.0)

        incumbency_fatigue_index = _clamp(incumbents * 0.55 + (12.0 - min(margin_pct, 12.0)) / 12.0, 0.0, 1.0)
        competitiveness_index = _clamp((8.0 - min(margin_pct, 8.0)) / 8.0, 0.0, 1.0)
        welfare_saturation_proxy = _clamp(
            (1.0 if "welfare" in " ".join([str(i).lower() for i in constituency.get("keyIssues", [])]) else 0.45)
            + (turnout / 100.0) * 0.2
            + (0.1 if registered > 300000 else 0.0),
            0.0,
            1.0,
        )
        demographic_fractionalization_proxy = _clamp(
            0.4 + issues * 0.07 + (0.15 if constituency.get("reservedFor") in {"SC", "ST"} else 0.0),
            0.0,
            1.0,
        )
        swing_signal = _safe_num(prediction.get("swingFrom2021"))

        return {
            "incumbency_fatigue_index": round(incumbency_fatigue_index, 3),
            "competitiveness_index": round(competitiveness_index, 3),
            "welfare_saturation_proxy": round(welfare_saturation_proxy, 3),
            "demographic_fractionalization_proxy": round(demographic_fractionalization_proxy, 3),
            "swing_signal": round(swing_signal, 3),
            "margin_pct_2021": round(margin_pct, 3),
        }

    def get_simulation_types(self) -> List[Dict]:
        return [
            {
                "type": "baseline",
                "title": "Baseline",
                "description": "No extra swing; uses current predictor priors.",
            },
            {
                "type": "anti_incumbency",
                "title": "Anti-incumbency",
                "description": "Soft anti-ruling swing with higher challenger momentum.",
            },
            {
                "type": "youth_surge",
                "title": "Youth Surge",
                "description": "Higher third-front movement among younger voters.",
            },
            {
                "type": "leadership_wave_spa",
                "title": "Leadership Wave (SPA)",
                "description": "Leadership-led consolidation toward SPA.",
            },
            {
                "type": "fragmented_mandate",
                "title": "Fragmented Mandate",
                "description": "Vote fragmentation rises; hung-style outcomes increase.",
            },
            {
                "type": "welfare_surge_spa",
                "title": "Welfare Surge",
                "description": "Higher welfare attribution lifts incumbent-bloc stability in welfare-heavy seats.",
            },
            {
                "type": "localized_anti_incumbency",
                "title": "Localized Anti-incumbency",
                "description": "Sharper anti-incumbency in marginal seats with high fatigue index.",
            },
        ]

    def get_constituency_snapshot(
        self,
        constituencies: List[Dict],
        ac_no: Optional[int] = None,
        name: Optional[str] = None,
    ) -> Optional[Dict]:
        target = None
        if name:
            wanted = _normalize_name(name)
            for constituency in constituencies:
                if _normalize_name(str(constituency.get("name", ""))) == wanted:
                    target = constituency
                    break

        if target is None and ac_no is not None:
            for constituency in constituencies:
                if int(constituency.get("acNo", 0)) == int(ac_no):
                    target = constituency
                    break

        if target is None:
            return None

        prediction = target.get("prediction", {})
        result = target.get("result2021", {})
        candidates = target.get("candidates2026", [])

        candidate_cards = []
        for candidate in candidates:
            candidate_cards.append(
                {
                    "name": candidate.get("name"),
                    "party": candidate.get("party"),
                    "alliance": candidate.get("alliance"),
                    "is_incumbent": bool(candidate.get("isIncumbent")),
                    "education": candidate.get("education"),
                    "assets": candidate.get("assets"),
                    "liabilities": candidate.get("liabilities"),
                    "cases": candidate.get("cases"),
                    "literacy": candidate.get("literacy"),
                    "age": candidate.get("age"),
                    "gender": candidate.get("gender"),
                    "profession": candidate.get("profession"),
                    "community": candidate.get("community"),
                    "eci_approved": bool(candidate.get("eciApproved", candidate.get("eci_approved", False))),
                    "party_approved": bool(candidate.get("partyApproved", candidate.get("party_approved", False))),
                    "nomination_status": candidate.get("nominationStatus", candidate.get("nomination_status")),
                    "nomination_date": candidate.get("nominationDate", candidate.get("nomination_date")),
                    "affidavit_url": candidate.get("affidavitUrl", candidate.get("affidavit_url")),
                    "eci_candidate_id": candidate.get("eciCandidateId", candidate.get("eci_candidate_id")),
                    "contact": candidate.get("contact"),
                    "website": candidate.get("website"),
                    "x_handle": candidate.get("xHandle", candidate.get("x_handle")),
                }
            )

        return {
            "ac_no": target.get("acNo"),
            "name": target.get("name"),
            "district": target.get("district"),
            "region": target.get("region"),
            "reserved_for": target.get("reservedFor"),
            "registered_voters_2021": target.get("registeredVoters2021"),
            "key_issues": target.get("keyIssues", []),
            "sentiment_score": target.get("sentimentScore", 0.0),
            "prediction": {
                "spa_win_prob": prediction.get("spaWinProb", 0),
                "nda_win_prob": prediction.get("ndaWinProb", 0),
                "tvk_win_prob": prediction.get("tvkWinProb", 0),
                "ntk_win_prob": prediction.get("ntkWinProb", 0),
                "others_win_prob": prediction.get("othersWinProb", 0),
                "predicted_winner": prediction.get("predictedWinner", "OTHERS"),
                "margin": prediction.get("margin", "tossup"),
                "swing_from_2021": prediction.get("swingFrom2021", 0),
            },
            "result_2021": {
                "winner": result.get("winner"),
                "winner_party": result.get("winnerParty"),
                "winner_votes": result.get("winnerVotes"),
                "runner_up": result.get("runnerUp"),
                "runner_up_party": result.get("runnerUpParty"),
                "runner_up_votes": result.get("runnerUpVotes"),
                "margin": result.get("margin"),
                "turnout_percent": result.get("turnoutPercent"),
            },
            "feature_snapshot": self._feature_snapshot(target),
            "candidate_cards": candidate_cards,
        }

    def get_party_trends(self, constituencies: List[Dict]) -> Dict:
        seats_2026 = {"SPA": 0, "NDA": 0, "TVK": 0, "NTK": 0, "OTHERS": 0}
        vote_proxy = {"SPA": 0.0, "NDA": 0.0, "TVK": 0.0, "NTK": 0.0, "OTHERS": 0.0}
        district_leads: Dict[str, Dict[str, int]] = {}

        for constituency in constituencies:
            prediction = constituency.get("prediction", {})
            winner = str(prediction.get("predictedWinner", "OTHERS"))
            if winner not in seats_2026:
                winner = "OTHERS"
            seats_2026[winner] += 1

            vote_proxy["SPA"] += _safe_num(prediction.get("spaWinProb"))
            vote_proxy["NDA"] += _safe_num(prediction.get("ndaWinProb"))
            vote_proxy["TVK"] += _safe_num(prediction.get("tvkWinProb"))
            vote_proxy["NTK"] += _safe_num(prediction.get("ntkWinProb"))
            vote_proxy["OTHERS"] += _safe_num(prediction.get("othersWinProb"))

            district = str(constituency.get("district", "Tamil Nadu"))
            district_leads.setdefault(district, {"SPA": 0, "NDA": 0, "TVK": 0, "NTK": 0, "OTHERS": 0})
            district_leads[district][winner] += 1

        total = max(1, len(constituencies))
        avg_vote_proxy = {k: round(v / total, 2) for k, v in vote_proxy.items()}

        top_districts = []
        for district, tally in district_leads.items():
            leader = max(tally, key=tally.get)
            top_districts.append({"district": district, "leader": leader, "lead_seats": tally[leader]})
        top_districts.sort(key=lambda row: row["lead_seats"], reverse=True)

        return {
            "seat_projection": seats_2026,
            "vote_share_proxy": avg_vote_proxy,
            "district_lead_map": top_districts[:25],
        }

    def run_simulation(self, constituencies: List[Dict], scenario_type: str, custom: Optional[Dict] = None) -> Dict:
        base_swing = self.scenario_presets.get(scenario_type, self.scenario_presets["baseline"]).copy()
        custom = custom or {}
        for key in ("spa", "nda", "tvk", "ntk"):
            if key in custom:
                base_swing[key] += _safe_num(custom[key])

        seat_tally = {"SPA": 0, "NDA": 0, "TVK": 0, "NTK": 0, "OTHERS": 0}
        battlegrounds = []

        for constituency in constituencies:
            prediction = constituency.get("prediction", {})
            features = self._feature_snapshot(constituency)
            structural_delta = {
                "spa": (
                    features["welfare_saturation_proxy"] * 1.6
                    - features["incumbency_fatigue_index"] * 1.5
                    + features["swing_signal"] * 0.14
                ),
                "nda": (
                    features["incumbency_fatigue_index"] * 1.2
                    + max(0.0, -features["swing_signal"]) * 0.12
                ),
                "tvk": (
                    features["demographic_fractionalization_proxy"] * 1.25
                    + features["competitiveness_index"] * 1.0
                ),
                "ntk": (
                    features["competitiveness_index"] * 0.8
                    + features["demographic_fractionalization_proxy"] * 0.6
                ),
            }
            adjusted = _renormalize(
                {
                    "SPA": _safe_num(prediction.get("spaWinProb")) + base_swing["spa"] + structural_delta["spa"],
                    "NDA": _safe_num(prediction.get("ndaWinProb")) + base_swing["nda"] + structural_delta["nda"],
                    "TVK": _safe_num(prediction.get("tvkWinProb")) + base_swing["tvk"] + structural_delta["tvk"],
                    "NTK": _safe_num(prediction.get("ntkWinProb")) + base_swing["ntk"] + structural_delta["ntk"],
                    "OTHERS": _safe_num(prediction.get("othersWinProb")),
                }
            )
            ordered = sorted(adjusted.items(), key=lambda item: item[1], reverse=True)
            winner = ordered[0][0]
            seat_tally[winner] += 1

            margin = ordered[0][1] - ordered[1][1]
            battlegrounds.append(
                {
                    "ac_no": constituency.get("acNo"),
                    "name": constituency.get("name"),
                    "district": constituency.get("district"),
                    "winner": winner,
                    "winner_prob": round(ordered[0][1], 2),
                    "runner_up": ordered[1][0],
                    "margin": round(margin, 2),
                    "features": features,
                }
            )

        battlegrounds.sort(key=lambda row: row["margin"])
        return {
            "scenario_type": scenario_type,
            "effective_swing": base_swing,
            "seat_tally": seat_tally,
            "magic_number": 118,
            "tossups": battlegrounds[:30],
        }
