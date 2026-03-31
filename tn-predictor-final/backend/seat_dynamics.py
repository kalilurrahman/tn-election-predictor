from __future__ import annotations

from typing import Dict, List


def _margin_pct(row: Dict) -> float:
    result = row.get("result2021", {}) or {}
    winner_votes = float(result.get("winnerVotes", 0) or 0)
    runner_votes = float(result.get("runnerUpVotes", 0) or 0)
    total = winner_votes + runner_votes
    if total <= 0:
        return 0.0
    return round(((winner_votes - runner_votes) / total) * 100, 2)


def _class_from_margin_pct(margin_pct: float) -> str:
    if margin_pct >= 15:
        return "safe"
    if margin_pct >= 5:
        return "swing"
    return "bellwether"


def _projected_margin_pct(row: Dict) -> float:
    prediction = row.get("prediction", {}) or {}
    probs = [
        float(prediction.get("spaWinProb", 0) or 0),
        float(prediction.get("ndaWinProb", 0) or 0),
        float(prediction.get("tvkWinProb", 0) or 0),
        float(prediction.get("ntkWinProb", 0) or 0),
        float(prediction.get("othersWinProb", 0) or 0),
    ]
    probs = sorted(probs, reverse=True)
    if len(probs) < 2:
        return 0.0
    return round(max(0.0, probs[0] - probs[1]), 2)


def _projected_class(row: Dict) -> str:
    margin_label = str((row.get("prediction", {}) or {}).get("margin", "")).lower().strip()
    mapping = {
        "safe": "safe",
        "lean": "swing",
        "tossup": "bellwether",
    }
    if margin_label in mapping:
        return mapping[margin_label]
    return _class_from_margin_pct(_projected_margin_pct(row))


def build_seat_dynamics(rows: List[Dict]) -> Dict:
    safe: List[Dict] = []
    swing: List[Dict] = []
    bellwether: List[Dict] = []
    transitions: Dict[str, int] = {}

    for row in rows:
        ac_no = int(row.get("acNo", 0) or 0)
        name = str(row.get("name", f"AC {ac_no}"))
        district = str(row.get("district", "Tamil Nadu"))
        swing_pct = float((row.get("prediction", {}) or {}).get("swingFrom2021", 0) or 0)
        margin_2021_pct = _margin_pct(row)
        projected_margin = _projected_margin_pct(row)
        class_2021 = _class_from_margin_pct(margin_2021_pct)
        class_2026 = _projected_class(row)
        winner_2021 = str((row.get("result2021", {}) or {}).get("winnerParty", ""))
        projected_winner = str((row.get("prediction", {}) or {}).get("predictedWinner", ""))

        item = {
            "ac_no": ac_no,
            "name": name,
            "district": district,
            "winner_2021": winner_2021,
            "projected_winner_2026": projected_winner,
            "margin_2021_pct": margin_2021_pct,
            "projected_margin_pct": projected_margin,
            "vote_swing_pct": round(swing_pct, 2),
            "class_2021": class_2021,
            "class_2026": class_2026,
        }

        if class_2026 == "safe":
            safe.append(item)
        elif class_2026 == "swing":
            swing.append(item)
        else:
            bellwether.append(item)

        key = f"{class_2021}->{class_2026}"
        transitions[key] = transitions.get(key, 0) + 1

    safe = sorted(safe, key=lambda x: (-x["projected_margin_pct"], abs(x["vote_swing_pct"]), x["name"]))
    swing = sorted(swing, key=lambda x: (abs(x["vote_swing_pct"]), x["projected_margin_pct"]))
    bellwether = sorted(bellwether, key=lambda x: (x["projected_margin_pct"], -abs(x["vote_swing_pct"])))

    return {
        "note": "Classifications are computed from available constituency-level margins and current projection fields. Refresh after candidate/result sync for latest values.",
        "counts_2026": {
            "safe": len(safe),
            "swing": len(swing),
            "bellwether": len(bellwether),
        },
        "transition_counts_2021_to_2026": transitions,
        "safe_seats": safe,
        "swing_seats": swing,
        "bellwether_seats": bellwether,
    }
