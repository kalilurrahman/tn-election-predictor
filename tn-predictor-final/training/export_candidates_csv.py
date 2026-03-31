import csv
import json
from pathlib import Path


def main():
    base = Path(__file__).resolve().parents[1]
    source = base / "public" / "constituencies_curated.json"
    if not source.exists():
        source = base / "public" / "constituencies.json"

    rows = json.loads(source.read_text(encoding="utf-8"))

    output = base / "public" / "tn_candidates_2026.csv"
    columns = [
        "ac_no", "ac_name", "district", "state", "region", "reserved_for",
        "candidate_name", "party", "alliance", "is_incumbent", "education", "profession", "age", "gender",
        "assets", "liabilities", "criminal_cases", "literacy", "community",
        "eci_approved", "party_approved", "nomination_status", "nomination_date",
        "affidavit_url", "eci_candidate_id", "contact", "website", "x_handle", "source", "predicted_winner",
    ]

    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()

        for constituency in rows:
            ac_no = int(constituency.get("acNo", 0) or 0)
            prediction = constituency.get("prediction", {})
            for candidate in constituency.get("candidates2026", []):
                writer.writerow(
                    {
                        "ac_no": ac_no,
                        "ac_name": constituency.get("name"),
                        "district": constituency.get("district"),
                        "state": "Tamil Nadu",
                        "region": constituency.get("region", "STATE"),
                        "reserved_for": constituency.get("reservedFor", "GEN"),
                        "candidate_name": candidate.get("name"),
                        "party": candidate.get("party"),
                        "alliance": candidate.get("alliance", "OTHERS"),
                        "is_incumbent": candidate.get("isIncumbent", candidate.get("is_incumbent", False)),
                        "education": candidate.get("education"),
                        "profession": candidate.get("profession"),
                        "age": candidate.get("age"),
                        "gender": candidate.get("gender"),
                        "assets": candidate.get("assets"),
                        "liabilities": candidate.get("liabilities"),
                        "criminal_cases": candidate.get("cases"),
                        "literacy": candidate.get("literacy"),
                        "community": candidate.get("community"),
                        "eci_approved": candidate.get("eciApproved", candidate.get("eci_approved", False)),
                        "party_approved": candidate.get("partyApproved", candidate.get("party_approved", False)),
                        "nomination_status": candidate.get("nominationStatus", candidate.get("nomination_status")),
                        "nomination_date": candidate.get("nominationDate", candidate.get("nomination_date")),
                        "affidavit_url": candidate.get("affidavitUrl", candidate.get("affidavit_url")),
                        "eci_candidate_id": candidate.get("eciCandidateId", candidate.get("eci_candidate_id")),
                        "contact": candidate.get("contact"),
                        "website": candidate.get("website"),
                        "x_handle": candidate.get("xHandle", candidate.get("x_handle")),
                        "source": candidate.get("source", "curated"),
                        "predicted_winner": prediction.get("predictedWinner"),
                    }
                )

    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
