"""
Website Scraper für Bundesliga-Vereins-Websites
Individuelle Strategie pro Verein basierend auf club_websites.md
"""

import os
import re
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup
import feedparser


@dataclass
class ClubNewsItem:
    """Ein einzelner News-Artikel von einer Vereins-Website."""
    club_id: str
    club_name: str
    title: str
    url: str
    published_at: datetime
    summary: str
    content: str = ""
    source_type: str = "website"  # "website", "rss", "press_release"
    scraped_at: datetime = field(default_factory=datetime.now)
    content_hash: str = ""  # Für Deduplizierung
    
    def __post_init__(self):
        if not self.content_hash and self.url:
            self.content_hash = hashlib.md5(self.url.encode()).hexdigest()[:12]


class BundesligaWebScraper:
    """
    Scraper für alle 18 Bundesliga-Vereins-Websites.
    Individuelle Konfiguration pro Verein (RSS, News-URL, etc.)
    """
    
    def __init__(self, timeout: int = 15):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "de-DE,de;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        self.timeout = timeout
    
    def _fetch_html(self, url: str) -> Optional[BeautifulSoup]:
        """Fetches and parses HTML from URL."""
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            print(f"  ✗ Fehler beim Abrufen von {url}: {e}")
            return None
    
    def _fetch_rss(self, url: str) -> list[dict]:
        """Parst einen RSS/Atom Feed."""
        try:
            feed = feedparser.parse(url)
            entries = []
            for entry in feed.entries[:20]:  # Max 20 Items
                entries.append({
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", ""),
                    "content": entry.get("content", [{}])[0].get("value", ""),
                })
            return entries
        except Exception as e:
            print(f"  ✗ RSS-Feed Fehler {url}: {e}")
            return []
    
    def scrape_club_website(self, config: dict) -> list[ClubNewsItem]:
        """
        Scrapt eine Vereins-Website basierend auf individueller Konfiguration.
        
        Args:
            config: Dict mit club_id, name, website, news_url, rss_url
            
        Returns:
            Liste von ClubNewsItem-Objekten
        """
        club_id = config["club_id"]
        club_name = config["name"]
        results = []
        
        print(f"\n🔍 Scraping {club_name} ({club_id})...")
        
        # 1. RSS Feed versuchen (wenn vorhanden)
        if config.get("rss_url"):
            print(f"  → RSS Feed: {config['rss_url']}")
            rss_items = self._fetch_rss(config["rss_url"])
            for item in rss_items:
                published = self._parse_date(item.get("published", ""))
                news_item = ClubNewsItem(
                    club_id=club_id,
                    club_name=club_name,
                    title=self._clean_text(item["title"]),
                    url=item["url"],
                    published_at=published,
                    summary=self._clean_text(item["summary"]),
                    content=self._clean_text(item["content"]),
                    source_type="rss"
                )
                results.append(news_item)
            print(f"    ✓ {len(rss_items)} RSS-Artikel gefunden")
        
        # 2. News-Pressemitteilungen scrapen (wenn vorhanden)
        if config.get("news_url"):
            print(f"  → News-Presse: {config['news_url']}")
            news_items = self._scrape_news_page(config["news_url"], config.get("news_selectors", {}))
            for item in news_items:
                item.club_id = club_id
                item.club_name = club_name
                item.source_type = "website"
            results.extend(news_items)
            print(f"    ✓ {len(news_items)} Website-Artikel gefunden")
        
        # 3. Pressemitteilungen-Seite (falls separate URL)
        if config.get("press_url"):
            print(f"  → Pressemitteilungen: {config['press_url']}")
            press_items = self._scrape_news_page(config["press_url"], config.get("press_selectors", {}))
            for item in press_items:
                item.club_id = club_id
                item.club_name = club_name
                item.source_type = "press_release"
            results.extend(press_items)
            print(f"    ✓ {len(press_items)} Pressemitteilungen gefunden")
        
        print(f"  📊 Gesamt: {len(results)} Artikel")
        return results
    
    def _scrape_news_page(self, url: str, selectors: dict = None) -> list[ClubNewsItem]:
        """
        Scraped eine News-Übersichtsseite.
        Versucht automatisch News-Links zu finden.
        """
        soup = self._fetch_html(url)
        if not soup:
            return []
        
        items = []
        selectors = selectors or {}
        
        # Versuche verschiedene Selektoren
        news_container = None
        container_val = selectors.get("container", [
            "article", ".news-list", ".news-overview",
            ".article-list", "[class*='news']", "main"
        ])
        # String in Liste normalisieren
        if isinstance(container_val, str):
            container_val = [container_val]
        for selector in container_val:
            try:
                news_container = soup.select_one(selector)
            except Exception:
                news_container = None
            if news_container:
                break
        
        if not news_container:
            news_container = soup
        
        # Links finden
        article_links = news_container.select("a[href*='news']")
        if not article_links:
            article_links = news_container.select("a[href*='article']")
        if not article_links:
            article_links = news_container.select("a[href*='aktuelles']")
        if not article_links:
            article_links = news_container.find_all("a", href=True)
        
        seen_urls = set()
        for link in article_links[:30]:  # Max 30 Links
            href = link.get("href", "")
            if not href or href.startswith("#") or "javascript" in href:
                continue
            
            # Relative URLs auflösen
            if not href.startswith("http"):
                from urllib.parse import urljoin
                href = urljoin(url, href)
            
            # Nur interne Links
            if "://" in href and self._get_domain(href) != self._get_domain(url):
                continue
            
            title = link.get_text(strip=True)
            if len(title) < 10:  # Zu kurze Titel überspringen
                continue
            
            if href in seen_urls:
                continue
            seen_urls.add(href)
            
            # Versuche Datum zu finden
            date_elem = link.find_parent().find_next_sibling()
            published = self._parse_date("")
            
            item = ClubNewsItem(
                club_id="",
                club_name="",
                title=self._clean_text(title),
                url=href,
                published_at=published,
                summary="",
                content="",
                source_type="website"
            )
            items.append(item)
        
        return items
    
    def _scrape_article_content(self, url: str) -> str:
        """Holt den vollständigen Artikel-Inhalt."""
        soup = self._fetch_html(url)
        if not soup:
            return ""
        
        # Versuche article-Tag oder main
        article = soup.select_one("article") or soup.select_one("main") or soup
        
        # Entferne Script- und Style-Tags
        for tag in article.find_all(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        
        text = article.get_text(separator="\n", strip=True)
        return self._clean_text(text)
    
    def _get_domain(self, url: str) -> str:
        """Extrahiert die Domain aus einer URL."""
        from urllib.parse import urlparse
        return urlparse(url).netloc
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parst ein Datums-String in datetime."""
        if not date_str:
            return datetime.now()
        
        # Versuche verschiedene Formate
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d.%m.%Y",
            "%d.%m.%Y %H:%M",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except:
                continue
        
        return datetime.now()
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Entfernt überflüssige Whitespaces und HTML-Reste."""
        if not text:
            return ""
        # HTML Tags entfernen
        text = re.sub(r'<[^>]+>', ' ', text)
        # Multiple Whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


# ============================================================
# Scraper-Konfiguration pro Bundesligist
# ============================================================

def get_club_configs() -> list[dict]:
    """
    Gibt die Scraper-Konfiguration für alle 18 Bundesligisten zurück.
    Wird aus club_websites.md gelesen (falls vorhanden)
    oder mit Default-Werten geladen.
    """
    return [
        {
            "club_id": "fc_bayern",
            "name": "FC Bayern München",
            "website": "https://fcbayern.com",
            "news_url": "https://fcbayern.com/news",
            "rss_url": "",  # ToDo: Recherche nötig
            "press_url": "https://fcbayern.com/de/presse",
            "news_selectors": {"container": "article"},
            "press_selectors": {"container": ".press-list"},
        },
        {
            "club_id": "bvb",
            "name": "Borussia Dortmund",
            "website": "https://borussia.de",
            "news_url": "https://borussia.de/news",
            "rss_url": "",  # ToDo
            "press_url": "",
            "news_selectors": {"container": ".news-list"},
        },
        {
            "club_id": "rb_leipzig",
            "name": "RB Leipzig",
            "website": "https://dierotenbullen.com",
            "news_url": "https://dierotenbullen.com/news",
            "rss_url": "",
            "press_url": "",
            "news_selectors": {"container": "article"},
        },
        {
            "club_id": "bayer_leverkusen",
            "name": "Bayer 04 Leverkusen",
            "website": "https://bayer04.de",
            "news_url": "https://bayer04.de/news",
            "rss_url": "",
            "press_url": "",
            "news_selectors": {"container": ".news"},
        },
        {
            "club_id": "eintracht",
            "name": "Eintracht Frankfurt",
            "website": "https://eintracht.de",
            "news_url": "https://eintracht.de/aktuelles",
            "rss_url": "",
            "press_url": "",
            "news_selectors": {"container": ".news-list"},
        },
        {
            "club_id": "vfb_stuttgart",
            "name": "VfB Stuttgart",
            "website": "https://vfb.de",
            "news_url": "https://vfb.de/news",
            "rss_url": "",
            "press_url": "",
            "news_selectors": {"container": "article"},
        },
        {
            "club_id": "sc_freiburg",
            "name": "SC Freiburg",
            "website": "https://scfreiburg.com",
            "news_url": "https://scfreiburg.com/news",
            "rss_url": "",
            "press_url": "",
            "news_selectors": {"container": ".news"},
        },
        {
            "club_id": "union_berlin",
            "name": "1. FC Union Berlin",
            "website": "https://fc-union-berlin.de",
            "news_url": "https://fc-union-berlin.de/news",
            "rss_url": "",
            "press_url": "",
            "news_selectors": {"container": "article"},
        },
        {
            "club_id": "vfl_wolfsburg",
            "name": "VfL Wolfsburg",
            "website": "https://vfl-wolfsburg.de",
            "news_url": "https://vfl-wolfsburg.de/news",
            "rss_url": "",
            "press_url": "",
            "news_selectors": {"container": ".news-list"},
        },
        {
            "club_id": "mainz_05",
            "name": "Mainz 05",
            "website": "https://mainz05.de",
            "news_url": "https://mainz05.de/news",
            "rss_url": "",
            "press_url": "",
            "news_selectors": {"container": "article"},
        },
        {
            "club_id": "borussia_mg",
            "name": "Borussia Mönchengladbach",
            "website": "https://borussia.de",
            "news_url": "https://borussia.de/news",
            "rss_url": "",
            "press_url": "",
            "news_selectors": {"container": ".news"},
        },
        {
            "club_id": "fc_augsburg",
            "name": "FC Augsburg",
            "website": "https://fcaugsburg.de",
            "news_url": "https://fcaugsburg.de/news",
            "rss_url": "",
            "press_url": "",
            "news_selectors": {"container": "article"},
        },
        {
            "club_id": "fc_heidenheim",
            "name": "1. FC Heidenheim",
            "website": "https://fc-heidenheim.de",
            "news_url": "https://fc-heidenheim.de/news",
            "rss_url": "",
            "press_url": "",
            "news_selectors": {"container": ".news"},
        },
        {
            "club_id": "tsg_hoffenheim",
            "name": "TSG Hoffenheim",
            "website": "https://tsg-hoffenheim.de",
            "news_url": "https://tsg-hoffenheim.de/news",
            "rss_url": "",
            "press_url": "",
            "news_selectors": {"container": "article"},
        },
        {
            "club_id": "fc_st_pauli",
            "name": "FC St. Pauli",
            "website": "https://fcstpauli.com",
            "news_url": "https://fcstpauli.com/news",
            "rss_url": "",
            "press_url": "https://fcstpauli.com/presse",
            "news_selectors": {"container": ".news-list"},
            "press_selectors": {"container": ".press-list"},
        },
        {
            "club_id": "werder_bremen",
            "name": "SV Werder Bremen",
            "website": "https://werder.de",
            "news_url": "https://werder.de/news",
            "rss_url": "",
            "press_url": "https://werder.de/presse",
            "news_selectors": {"container": "article"},
        },
        {
            "club_id": "holstein_kiel",
            "name": "Holstein Kiel",
            "website": "https://holstein-kiel.de",
            "news_url": "https://holstein-kiel.de/news",
            "rss_url": "",
            "press_url": "",
            "news_selectors": {"container": ".news"},
        },
        {
            "club_id": "vfl_bochum",
            "name": "VfL Bochum",
            "website": "https://vflbochum.de",
            "news_url": "https://vflbochum.de/news",
            "rss_url": "",
            "press_url": "",
            "news_selectors": {"container": "article"},
        },
    ]


# ============================================================
# CLI Interface
# ============================================================

if __name__ == "__main__":
    import argparse
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description="Bundesliga Website Scraper")
    parser.add_argument("--clubs", "-c", nargs="+", 
                        help="Club IDs zum Scrapen (alle wenn weggelassen)")
    parser.add_argument("--output", "-o", default="data/scraped_news.json",
                        help="Output-Datei")
    parser.add_argument("--rss-only", action="store_true",
                        help="Nur RSS-Feeds scrapen")
    parser.add_argument("--verbose", "-v", action="store_true")
    
    args = parser.parse_args()
    
    scraper = BundesligaWebScraper()
    configs = get_club_configs()
    
    # Filtern falls Clubs angegeben
    if args.clubs:
        configs = [c for c in configs if c["club_id"] in args.clubs]
    
    all_news = []
    for config in configs:
        if args.rss_only and not config.get("rss_url"):
            continue
        
        items = scraper.scrape_club_website(config)
        all_news.extend(items)
    
    # Speichern als JSON
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_path, "w") as f:
        json.dump([item.__dict__ for item in all_news], f, indent=2, default=str)
    
    print(f"\n✅ {len(all_news)} Artikel gespeichert in {output_path}")
