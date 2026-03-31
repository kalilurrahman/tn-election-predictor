import re
from typing import Dict, List


def _strip_html(text: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", no_tags).strip()


def parse_eci_html_candidates(html: str, source_url: str) -> List[Dict]:
    """
    Best-effort parser for ECI-like tabular candidate pages.
    Expected columns (case-insensitive, partial matching):
    - AC No / Constituency / Candidate Name / Party / Status / Affidavit
    """
    tables = re.findall(r"<table[\s\S]*?</table>", html or "", flags=re.IGNORECASE)
    parsed: List[Dict] = []

    for table in tables:
        rows = re.findall(r"<tr[\s\S]*?</tr>", table, flags=re.IGNORECASE)
        if len(rows) < 2:
            continue

        header_cells = re.findall(r"<t[hd][^>]*>([\s\S]*?)</t[hd]>", rows[0], flags=re.IGNORECASE)
        headers = [_strip_html(cell).lower() for cell in header_cells]
        if not headers:
            continue

        def index_of(*keywords: str) -> int:
            for idx, header in enumerate(headers):
                if any(keyword in header for keyword in keywords):
                    return idx
            return -1

        idx_ac_no = index_of("ac", "constituency no")
        idx_constituency = index_of("constituency", "assembly constituency")
        idx_candidate = index_of("candidate", "name")
        idx_party = index_of("party")
        idx_status = index_of("status", "nomination")
        idx_affidavit = index_of("affidavit")

        if idx_candidate < 0:
            continue

        for row in rows[1:]:
            cells = re.findall(r"<t[dh][^>]*>([\s\S]*?)</t[dh]>", row, flags=re.IGNORECASE)
            if not cells:
                continue

            def get_value(index: int) -> str:
                if index < 0 or index >= len(cells):
                    return ""
                return _strip_html(cells[index])

            def get_link(index: int) -> str:
                if index < 0 or index >= len(cells):
                    return ""
                href_match = re.search(r'href=["\']([^"\']+)["\']', cells[index], flags=re.IGNORECASE)
                return href_match.group(1).strip() if href_match else ""

            candidate_name = get_value(idx_candidate)
            if not candidate_name:
                continue

            ac_no_text = get_value(idx_ac_no)
            ac_no_match = re.search(r"\d+", ac_no_text)
            ac_no = int(ac_no_match.group(0)) if ac_no_match else 0

            nomination_status = get_value(idx_status) or "confirmed"
            affidavit_url = get_link(idx_affidavit)

            parsed.append(
                {
                    "ac_no": ac_no,
                    "constituency_name": get_value(idx_constituency),
                    "candidate_name": candidate_name,
                    "party": get_value(idx_party) or "IND",
                    "nomination_status": nomination_status,
                    "affidavit_url": affidavit_url,
                    "eci_approved": nomination_status.lower() in {"confirmed", "accepted", "valid"},
                    "validation_reports": [source_url],
                    "source": "eci_html",
                }
            )

    return parsed

