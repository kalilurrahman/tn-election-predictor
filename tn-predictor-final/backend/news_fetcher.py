import html
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List

import requests


class NewsScraper:
    def __init__(self):
        self.base_url = "https://news.google.com/rss/search"

    def get_constituency_news(self, name: str, district: str) -> List[Dict]:
        query = f'"{name}" Tamil Nadu election OR "{name} constituency" OR "{district}" "{name}"'
        news_results = self._fetch(query, max_items=8)
        if news_results:
            return news_results
        return self.get_district_news(district)

    def get_district_news(self, district: str) -> List[Dict]:
        query = f'"{district}" Tamil Nadu election'
        return self._fetch(query, max_items=5)

    def _fetch(self, query: str, max_items: int) -> List[Dict]:
        params = {
            "q": query,
            "hl": "en-IN",
            "gl": "IN",
            "ceid": "IN:en",
        }
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        }

        try:
            response = requests.get(self.base_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            root = ET.fromstring(response.text)
        except Exception as exc:
            print(f"Scraper error for query '{query}': {exc}")
            return []

        seen_titles = set()
        items: List[Dict] = []

        for item in root.findall("./channel/item"):
            title = html.unescape((item.findtext("title") or "").strip())
            link = (item.findtext("link") or "").strip()
            published = (item.findtext("pubDate") or "").strip()
            source = html.unescape((item.findtext("source") or "News").strip())

            if not title or title in seen_titles:
                continue

            items.append(
                {
                    "title": title,
                    "link": link,
                    "published": published or datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
                    "source": source or "News",
                }
            )
            seen_titles.add(title)

            if len(items) >= max_items:
                break

        return items
