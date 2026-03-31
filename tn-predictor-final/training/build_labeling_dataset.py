import argparse
import json
from pathlib import Path

from backend.news_fetcher import NewsScraper
from backend.signal_pipeline import SentimentEngine


def main():
    parser = argparse.ArgumentParser(description="Build a JSONL labeling dataset from constituency headlines.")
    parser.add_argument("--input", default="public/constituencies.json")
    parser.add_argument("--output", default="training/headline_labels.jsonl")
    parser.add_argument("--limit", type=int, default=25, help="Number of constituencies to sample")
    parser.add_argument("--remote", action="store_true", help="Prefer Hugging Face sentiment during export")
    args = parser.parse_args()

    constituencies = json.loads(Path(args.input).read_text(encoding="utf-8"))
    scraper = NewsScraper()
    sentiment = SentimentEngine()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    with output_path.open("w", encoding="utf-8") as handle:
        for constituency in constituencies[: args.limit]:
            name = constituency.get("name", "Unknown")
            district = constituency.get("district", "Tamil Nadu")
            issues = constituency.get("keyIssues", [])
            candidates = [c.get("name", "") for c in constituency.get("candidates2026", [])]

            articles = scraper.get_constituency_news(name, district)
            analysis = sentiment.analyze_news(
                articles,
                constituency_name=name,
                district_name=district,
                issues=issues,
                candidates=candidates,
                prefer_remote=args.remote,
            )

            for article in analysis["news"]:
                row = {
                    "constituency": name,
                    "district": district,
                    "headline": article["title"],
                    "published": article.get("published"),
                    "source": article.get("source"),
                    "model_sentiment_score": article.get("sentiment_score"),
                    "model_sentiment_label": article.get("sentiment_label"),
                    "human_sentiment_label": "",
                    "alliance_impact": "",
                    "notes": "",
                }
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                written += 1

    print(f"Wrote {written} labeling rows to {output_path}")


if __name__ == "__main__":
    main()
