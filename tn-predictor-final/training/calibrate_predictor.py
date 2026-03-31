import argparse
import json
import math
from pathlib import Path


def load_rows(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def score_row(row, scale: float, bias: float):
    sentiment = float(row.get("model_sentiment_score", 0.0))
    article_count = float(row.get("article_count", 1.0))
    diversity = float(row.get("source_diversity", 1.0))
    raw = (sentiment * scale) + (math.log1p(article_count) * 0.08) + (diversity * 0.04) + bias
    return 1.0 / (1.0 + math.exp(-raw))


def target_from_row(row):
    label = str(row.get("alliance_impact", "")).strip().upper()
    if label in {"SPA", "POSITIVE"}:
        return 1.0
    if label in {"NDA", "NEGATIVE"}:
        return 0.0
    return 0.5


def loss(rows, scale: float, bias: float):
    total = 0.0
    for row in rows:
        target = target_from_row(row)
        pred = min(0.999, max(0.001, score_row(row, scale, bias)))
        total += -(target * math.log(pred) + (1 - target) * math.log(1 - pred))
    return total / max(1, len(rows))


def main():
    parser = argparse.ArgumentParser(description="Calibrate lightweight predictor weights from labeled headline data.")
    parser.add_argument("--input", default="training/headline_training_rows.jsonl")
    parser.add_argument("--output", default="training/calibration_result.json")
    args = parser.parse_args()

    rows = load_rows(Path(args.input))
    if not rows:
        raise SystemExit("No labeled rows found.")

    best = None
    for scale in [x / 10 for x in range(4, 21)]:
        for bias in [x / 20 for x in range(-10, 11)]:
            current_loss = loss(rows, scale, bias)
            if best is None or current_loss < best["loss"]:
                best = {"scale": scale, "bias": bias, "loss": round(current_loss, 6)}

    Path(args.output).write_text(json.dumps(best, indent=2), encoding="utf-8")
    print(json.dumps(best, indent=2))


if __name__ == "__main__":
    main()
