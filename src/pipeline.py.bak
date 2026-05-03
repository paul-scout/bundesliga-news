"""Main pipeline: Scraped alle Quellen und generiert das Portal."""

import json
from pathlib import Path
from datetime import datetime

from .scrapers.website_scraper import BundesligaWebScraper, get_club_configs
from .portal import generate_portal


def main(scrape: bool = True, clubs: list[str] = None, output: str = "docs/index.html"):
    """
    Haupteinstieg: Scraped + Generiert Portal.
    
    Args:
        scrape: Ob gescraped werden soll oder nur Portal aus Cache
        clubs: Liste von Club-IDs (None = alle)
        output: Output-Pfad für HTML
    """
    print(f"\n⚽ Bundesliga News Pipeline — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    all_articles = []
    
    if scrape:
        scraper = BundesligaWebScraper()
        configs = get_club_configs()
        
        # Filtern falls spezifische Clubs
        if clubs:
            configs = [c for c in configs if c["club_id"] in clubs]
        
        for config in configs:
            items = scraper.scrape_club_website(config)
            all_articles.extend(items)
        
        # Cache speichern
        cache_path = Path("data/scraped_news.json")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump([a.__dict__ for a in all_articles], f, indent=2, default=str)
        print(f"\n💾 {len(all_articles)} Artikel gecached")
    else:
        # Aus Cache laden
        cache_path = Path("data/scraped_news.json")
        if cache_path.exists():
            with open(cache_path) as f:
                from .scrapers.website_scraper import ClubNewsItem
                raw = json.load(f)
            all_articles = [ClubNewsItem(**r) for r in raw]
            print(f"📂 {len(all_articles)} Artikel aus Cache geladen")
        else:
            print("⚠️  Kein Cache — starte mit --scrape")
            return
    
    # Portal generieren
    output_path = generate_portal(all_articles, output, days_back=3)
    print(f"\n🌐 Portal: {output_path}")
    print(f"📊 Artikel: {len(all_articles)} | Vereine: {len(set(a.club_id for a in all_articles))}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Bundesliga News Pipeline")
    parser.add_argument("--scrape", action="store_true", default=True)
    parser.add_argument("--no-scrape", dest="scrape", action="store_false")
    parser.add_argument("--clubs", "-c", nargs="+")
    parser.add_argument("--output", "-o", default="docs/index.html")
    
    args = parser.parse_args()
    main(scrape=args.scrape, clubs=args.clubs, output=args.output)
