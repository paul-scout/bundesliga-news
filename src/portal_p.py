"""
Generiert ein statisches HTML-Portal aus den gesammelten News-Artikeln.
Design: SuperDesign / Gstack Frontend-Design Skill — Modern Dark Mode
Täglich neu aufrufbar — output: docs/index.html (GitHub Pages ready)
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from scrapers.website_scraper import BundesligaWebScraper, get_club_configs, ClubNewsItem
from youtube.scraper import BundesligaYouTubeScraper


CLUB_BADGES = {
    "fc_bayern": "🔴 FC Bayern",
    "bvb": "🟡 BVB",
    "rb_leipzig": "🔴 RBL",
    "bayer_leverkusen": "🔴 Bayer",
    "eintracht": "⚽ Eintracht",
    "vfb_stuttgart": "⚽ VfB",
    "sc_freiburg": "⚽ Freiburg",
    "union_berlin": "⚽ Union",
    "vfl_wolfsburg": "⚽ Wolfsburg",
    "mainz_05": "⚽ Mainz",
    "borussia_mg": "⚽ Gladbach",
    "fc_augsburg": "⚽ Augsburg",
    "fc_heidenheim": "⚽ Heidenheim",
    "tsg_hoffenheim": "⚽ Hoffenheim",
    "fc_st_pauli": "⚽ St. Pauli",
    "werder_bremen": "⚽ Werder",
    "holstein_kiel": "⚽ Kiel",
    "vfl_bochum": "⚽ Bochum",
}

# Vereinsfarben (oklch für moderne Farbdefinition)
CLUB_COLORS = {
    "fc_bayern": "#0066B2",
    "bvb": "#FFE500",
    "rb_leipzig": "#FF0018",
    "bayer_leverkusen": "#E2000A",
    "eintracht": "#FF0000",
    "vfb_stuttgart": "#FFFFFF",
    "sc_freiburg": "#FFFFFF",
    "union_berlin": "#DD00CC",
    "vfl_wolfsburg": "#119C4B",
    "mainz_05": "#FF0000",
    "borussia_mg": "#FFFFFF",
    "fc_augsburg": "#FFFFFF",
    "fc_heidenheim": "#0072C3",
    "tsg_hoffenheim": "#2264DC",
    "fc_st_pauli": "#E20613",
    "werder_bremen": "#008C40",
    "holstein_kiel": "#0066BD",
    "vfl_bochum": "#005CA9",
}


def generate_portal(
    scraped_articles: list[ClubNewsItem],
    output_path: str = "docs/index.html",
    title: str = "Bundesliga News Portal",
    days_back: int = 3
) -> str:
    """
    Generiert eine statische HTML-Seite aus den gesammelten Artikeln.
    Design: Modern Dark Mode — SuperDesign Guidelines
    """
    
    # Filter: nur Artikel der letzten Tage
    recent_articles = []
    for a in scraped_articles:
        pa = a.published_at
        if pa and isinstance(pa, str):
            try: pa = datetime.fromisoformat(pa.replace("Z","+00:00"))
            except: pa = None
        if pa and isinstance(pa, datetime) and (datetime.now() - pa).days <= days_back:
            recent_articles.append(a)
    
    # Sortiere nach Datum absteigend
    recent_articles.sort(key=lambda a: a.published_at, reverse=True)
    
    # Gruppiere nach Club
    by_club: dict[str, list[ClubNewsItem]] = {}
    for article in recent_articles:
        if article.club_id not in by_club:
            by_club[article.club_id] = []
        by_club[article.club_id].append(article)
    
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    article_count = len(recent_articles)
    club_count = len(by_club)
    
    # Club-Navigation
    club_nav_items = ""
    for club_id in sorted(by_club.keys()):
        club_name = by_club[club_id][0].club_name
        short_name = club_name.split()[-1]  # Letztes Wort
        club_nav_items += f'<a href="#{club_id}" class="nav-item">{short_name}</a>'
    
    # Club-Sektionen
    club_sections = ""
    for club_id in sorted(by_club.keys()):
        club_articles = by_club[club_id]
        club_name = club_articles[0].club_name
        color = CLUB_COLORS.get(club_id, "#333333")
        badge = CLUB_BADGES.get(club_id, club_name)
        
        article_cards = ""
        for article in club_articles[:10]:
            date_str = article.published_at.strftime("%d.%m.")
            summary = _truncate(article.summary, 150)
            source_icon = "🌐" if article.source_type == "website" else "▶️"
            
            article_cards += f"""
            <article class="news-card" style="--club-color: {color}">
                <div class="card-meta">
                    <span class="card-date">{date_str}</span>
                    <span class="card-source">{source_icon}</span>
                </div>
                <h3 class="card-title">
                    <a href="{article.url}" target="_blank" rel="noopener">{article.title}</a>
                </h3>
                <p class="card-summary">{summary}</p>
                <div class="card-accent" style="background: {color}"></div>
            </article>"""
        
        club_sections += f"""
        <section class="club-section" id="{club_id}">
            <div class="club-header">
                <div class="club-title">
                    <span class="club-dot" style="background: {color}"></span>
                    <h2>{club_name}</h2>
                </div>
                <span class="club-count">{len(club_articles)} Artikel</span>
            </div>
            <div class="news-grid">{article_cards}
            </div>
        </section>"""
    
    if not club_sections:
        club_sections = """
        <div class="empty-state">
            <p>Keine aktuellen News gefunden.</p>
            <code>python -m bundesliga_news.src.portal --scrape</code>
        </div>"""
    
    # Logo SVG (Ball)
    logo_svg = """<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a15 15 0 0 1 4 10 15 15 0 0 1-4 10 15 15 0 0 1-4-10 15 15 0 0 1 4-10z"/><path d="M2 12h20"/></svg>"""
    
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="Alle Bundesliga News aus einem Guss — täglich automatisch aktualisiert.">
    
    <!-- Google Fonts: Inter + JetBrains Mono -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    
    <style>
        /* ─── Design Tokens ─── */
        :root {{
            --bg-base: #09090b;
            --bg-surface: #18181b;
            --bg-elevated: #27272a;
            --border: #3f3f46;
            --border-subtle: #27272a;
            --text-primary: #fafafa;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            --accent: #22c55e;
            --accent-muted: #166534;
            --radius: 0.75rem;
            --radius-sm: 0.5rem;
            --font-sans: 'Inter', system-ui, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
            --shadow: 0 1px 3px rgba(0,0,0,0.3);
            --transition: 200ms ease;
        }}
        
        /* ─── Reset & Base ─── */
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
        
        html {{ scroll-behavior: smooth; }}
        
        body {{
            font-family: var(--font-sans);
            background: var(--bg-base);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }}
        
        a {{ color: inherit; text-decoration: none; }}
        
        /* ─── Header ─── */
        .site-header {{
            background: var(--bg-surface);
            border-bottom: 1px solid var(--border-subtle);
            padding: 2rem 1.5rem;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(12px);
        }}
        
        .header-inner {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }}
        
        .logo {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .logo-icon {{
            color: var(--accent);
            display: flex;
        }}
        
        .logo h1 {{
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }}
        
        .logo span {{
            font-size: 0.8rem;
            color: var(--text-muted);
            font-weight: 400;
        }}
        
        .header-stats {{
            display: flex;
            gap: 1.5rem;
        }}
        
        .stat {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--accent);
            font-variant-numeric: tabular-nums;
        }}
        
        .stat-label {{
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
        }}
        
        /* ─── Nav ─── */
        .site-nav {{
            background: var(--bg-surface);
            border-bottom: 1px solid var(--border-subtle);
            padding: 0.75rem 1.5rem;
            overflow-x: auto;
        }}
        
        .club-nav {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            gap: 0.5rem;
        }}
        
        .nav-item {{
            display: inline-flex;
            align-items: center;
            padding: 0.4rem 0.75rem;
            border-radius: var(--radius-sm);
            font-size: 0.8rem;
            font-weight: 500;
            color: var(--text-secondary);
            white-space: nowrap;
            transition: all var(--transition);
            border: 1px solid transparent;
        }}
        
        .nav-item:hover {{
            background: var(--bg-elevated);
            color: var(--text-primary);
            border-color: var(--border);
        }}
        
        /* ─── Main ─── */
        main {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 1.5rem;
        }}
        
        /* ─── Club Sections ─── */
        .club-section {{
            margin-bottom: 2.5rem;
        }}
        
        .club-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 0.75rem;
            margin-bottom: 1rem;
        }}
        
        .club-title {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .club-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }}
        
        .club-title h2 {{
            font-size: 1rem;
            font-weight: 600;
            letter-spacing: -0.01em;
        }}
        
        .club-count {{
            font-size: 0.75rem;
            color: var(--text-muted);
            font-family: var(--font-mono);
        }}
        
        /* ─── News Grid ─── */
        .news-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1rem;
        }}
        
        /* ─── News Card ─── */
        .news-card {{
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius);
            padding: 1.25rem;
            position: relative;
            overflow: hidden;
            transition: all var(--transition);
        }}
        
        .news-card:hover {{
            border-color: var(--border);
            transform: translateY(-2px);
            box-shadow: var(--shadow);
        }}
        
        .card-accent {{
            position: absolute;
            top: 0;
            left: 0;
            width: 3px;
            height: 100%;
            opacity: 0.6;
        }}
        
        .card-meta {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }}
        
        .card-date {{
            font-size: 0.75rem;
            color: var(--text-muted);
            font-family: var(--font-mono);
        }}
        
        .card-source {{
            font-size: 0.75rem;
        }}
        
        .card-title {{
            font-size: 0.95rem;
            font-weight: 600;
            line-height: 1.4;
            margin-bottom: 0.5rem;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        
        .card-title a {{
            color: var(--text-primary);
            transition: color var(--transition);
        }}
        
        .card-title a:hover {{
            color: var(--accent);
        }}
        
        .card-summary {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            line-height: 1.5;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        
        /* ─── Footer ─── */
        footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            font-size: 0.75rem;
            border-top: 1px solid var(--border-subtle);
            margin-top: 2rem;
        }}
        
        footer a {{ color: var(--text-muted); }}
        footer a:hover {{ color: var(--text-secondary); }}
        
        /* ─── Empty State ─── */
        .empty-state {{
            text-align: center;
            padding: 4rem 2rem;
            color: var(--text-muted);
        }}
        
        .empty-state code {{
            font-family: var(--font-mono);
            background: var(--bg-surface);
            padding: 0.5rem 1rem;
            border-radius: var(--radius-sm);
            display: inline-block;
            margin-top: 1rem;
        }}
        
        /* ─── Responsive ─── */
        @media (max-width: 768px) {{
            .header-stats {{ display: none; }}
            .header-inner {{ flex-direction: column; align-items: flex-start; }}
            .news-grid {{ grid-template-columns: 1fr; }}
            .club-nav {{ flex-wrap: nowrap; }}
        }}
        
        /* ─── Animations ─── */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .news-card {{
            animation: fadeIn 400ms ease-out both;
        }}
        
        .news-grid .news-card:nth-child(2) {{ animation-delay: 50ms; }}
        .news-grid .news-card:nth-child(3) {{ animation-delay: 100ms; }}
        .news-grid .news-card:nth-child(4) {{ animation-delay: 150ms; }}
    </style>
</head>
<body>
    <header class="site-header">
        <div class="header-inner">
            <div class="logo">
                <div class="logo-icon">{logo_svg}</div>
                <div>
                    <h1>Bundesliga News</h1>
                    <span>Täglich automatisch</span>
                </div>
            </div>
            <div class="header-stats">
                <div class="stat">
                    <div class="stat-value">{article_count}</div>
                    <div class="stat-label">Artikel</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{club_count}</div>
                    <div class="stat-label">Vereine</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{generated_at.split()[-1]}</div>
                    <div class="stat-label">Letztes Update</div>
                </div>
            </div>
        </div>
    </header>
    
    <nav class="site-nav">
        <div class="club-nav">
            <a href="#top" class="nav-item">↑ Nach oben</a>
            {club_nav_items}
        </div>
    </nav>
    
    <main>
        {club_sections}
    </main>
    
    <footer>
        <p>⚽ Bundesliga News Portal — Quellen: Vereins-Websites + YouTube</p>
        <p>Automatisch generiert | Stand: {generated_at}</p>
    </footer>
    
    <script>
        // Smooth scroll + active nav highlighting
        document.querySelectorAll('.club-nav a[href^="#"]').forEach(link => {{
            link.addEventListener('click', e => {{
                e.preventDefault();
                const target = document.querySelector(link.getAttribute('href'));
                target?.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }});
        }});
        
        // Update active nav on scroll
        const sections = document.querySelectorAll('.club-section[id]');
        const navLinks = document.querySelectorAll('.club-nav a[href^="#"]');
        
        window.addEventListener('scroll', () => {{
            let current = '';
            sections.forEach(section => {{
                const sectionTop = section.offsetTop;
                if (scrollY >= sectionTop - 200) {{
                    current = section.getAttribute('id');
                }}
            }});
            navLinks.forEach(link => {{
                link.style.color = '';
                if (link.getAttribute('href') === '#' + current) {{
                    link.style.color = 'var(--accent)';
                }}
            }});
        }});
    </script>
</body>
</html>"""
    
    # Schreibe Datei
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    
    return str(output)


def _truncate(text: str, max_chars: int) -> str:
    """Kürzt Text sauber ab."""
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generiert Bundesliga News Portal HTML")
    parser.add_argument("--output", "-o", default="docs/index.html")
    parser.add_argument("--days", "-d", type=int, default=3)
    parser.add_argument("--scrape", action="store_true", help="Scrape alle Vereins-Websites zuerst")
    
    args = parser.parse_args()
    
    if args.scrape:
        print("🔍 Scraping alle Vereins-Websites...")
        scraper = BundesligaWebScraper()
        all_articles = []
        for config in get_club_configs():
            items = scraper.scrape_club_website(config)
            all_articles.extend(items)
        print(f"✅ {len(all_articles)} Artikel gesammelt")
    else:
        from pathlib import Path
        data_file = Path("data/scraped_news.json")
        if data_file.exists():
            with open(data_file) as f:
                raw = json.load(f)
            all_articles = [ClubNewsItem(**r) for r in raw]
        else:
            print("⚠️  Keine gecachten Daten. Nutze --scrape.")
            all_articles = []
    
    output = generate_portal(all_articles, args.output, days_back=args.days)
    print(f"🌐 Portal generiert: {output}")
