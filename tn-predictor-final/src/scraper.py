import requests
from bs4 import BeautifulSoup
import time
import random
from typing import List, Dict, Any, Optional

class ElectionScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.max_retries = 3
        self.delay_between_requests = (1, 3)

    def _make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, timeout=15, **kwargs)
                response.raise_for_status()
                time.sleep(random.uniform(*self.delay_between_requests))
                return response
            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    print(f"Max retries reached for {url}. Skipping.")
                    return None
        return None

    def scrape_custom_url(self, url: str) -> str:
        print(f"Scraping custom URL: {url}")
        response = self._make_request(url)
        if response:
            return response.text
        else:
            return f"Failed to retrieve content from {url}"

    def scrape_election_commission_candidates(self) -> List[Dict[str, str]]:
        print("Attempting to scrape ECI candidate data (Placeholder)...")
        dummy_candidates = [
            {"name": "Thiru. M.K. Stalin", "party": "DMK", "constituency": "Kolathur"},
            {"name": "Thiru. Edappadi K. Palaniswami", "party": "AIADMK", "constituency": "Edappadi"},
            {"name": "Thiru. K. Annamalai", "party": "BJP", "constituency": "Coimbatore South"},
            {"name": "Thiru. Kamal Haasan", "party": "Makkal Needhi Maiam", "constituency": "Coimbatore South"}
        ]
        print("Returning dummy candidate data for ECI scrape.")
        time.sleep(random.uniform(*self.delay_between_requests))
        return dummy_candidates

    def scrape_news_articles(self, query: str = "Tamil Nadu election", num_articles: int = 10) -> List[Dict[str, str]]:
        print(f"Scraping news articles for query: '{query}'")
        articles_data = []
        search_url = f"https://www.google.com/search?q={query}&tbm=nws"
        response = self._make_request(search_url)
        if not response:
            print("Failed to fetch news search results page.")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        headlines = soup.find_all('div', class_='n0jRee')
        sources = soup.find_all('div', class_='MgUUO')
        print(f"Found {len(headlines)} potential headlines and {len(sources)} potential sources.")

        for i in range(min(len(headlines), len(sources), num_articles)):
            headline_tag = headlines[i].find('a')
            headline = headline_tag.get_text(strip=True) if headline_tag else "N/A"
            link = headline_tag['href'] if headline_tag and 'href' in headline_tag.attrs else "#"
            source_info_tag = sources[i].find('div', class_='B6bxjd')
            if source_info_tag:
                source_time_parts = [tag.get_text(strip=True) for tag in source_info_tag.find_all('div')]
                source = source_time_parts[0] if source_time_parts else "N/A"
            else:
                source = "N/A"

            if headline != "N/A" and link != "#":
                if link.startswith('/url?q='):
                    link = link.split('/url?q=')[1].split('&sa=U')[0]
                articles_data.append({'title': headline, 'url': link, 'source': source, 'query': query})

        print(f"Scraped {len(articles_data)} articles.")
        time.sleep(random.uniform(*self.delay_between_requests))
        return articles_data

    def scrape_twitter_feed(self, keywords: str, count: int = 50) -> List[Dict[str, str]]:
        print(f"Attempting to scrape Twitter for keywords: '{keywords}' (Placeholder)...")
        dummy_tweets = [
            {"text": f"This is a dummy tweet about {keywords}.", "user": "DummyUser1", "date": "2026-04-04"},
            {"text": f"Another random thought on {keywords} from a fake account.", "user": "FakeTweeter", "date": "2026-04-04"}
        ] * (count // 2)
        print("Returning dummy Twitter data.")
        time.sleep(random.uniform(*self.delay_between_requests))
        return dummy_tweets

    def get_constituency_page_data(self, constituency_name: str) -> Dict[str, Any]:
        print(f"Scraping data for constituency: {constituency_name} (Placeholder)...")
        dummy_data = {
            "name": constituency_name,
            "district": "Chennai",
            "incumbent_mla": "Current MLA Name",
            "major_issues": ["Water Scarcity", "Infrastructure"],
            "key_parties": ["DMK", "AIADMK"]
        }
        print("Returning dummy constituency data.")
        time.sleep(random.uniform(*self.delay_between_requests))
        return dummy_data
