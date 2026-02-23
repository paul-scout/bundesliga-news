#!/usr/bin/env python3
"""
YouTube Video Finder für Bundesliga Pressekonferenzen
Sucht automatisch Videos zu Spielen
"""
from tavily import TavilyClient
import re
import os

# Tavily API Key (als Env oder hier setzen)
TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY', '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')

def extract_video_id(url):
    """Extrahiert YouTube Video ID aus URL"""
    patterns = [
        r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def search_videos(team1, team2, date=None):
    """Sucht Pressekonferenzen zu einem Spiel"""
    client = TavilyClient(api_key=TAVILY_API_KEY)
    
    results = {}
    
    # Suchbegriffe (mit Gegner für spezifischere Suche)
    queries = [
        f"{team1} Pressekonferenz nach dem Spiel {team2}",
        f"{team2} Pressekonferenz nach dem Spiel {team1}",
        f"{team1} Pressekonferenz vor dem Spiel {team2}",
        f"{team2} Pressekonferenz vor dem Spiel {team1}",
        f"{team1} Stimmen nach dem Spiel {team2}",
        f"Sportschau {team1} {team2}",
    ]
    
    for query in queries:
        try:
            response = client.search(query, max_results=3)
            for r in response.get('results', []):
                url = r.get('url', '')
                if 'youtube.com' in url or 'youtu.be' in url:
                    video_id = extract_video_id(url)
                    if video_id:
                        # Kategorie erkennen
                        if 'Pressekonferenz' in r.get('title', '') and 'nach' in r.get('title', '').lower():
                            key = f"{team1}_presse_nach"
                        elif 'Pressekonferenz' in r.get('title', '') and 'vor' in r.get('title', '').lower():
                            key = f"{team1}_presse_vor"
                        elif 'Sportschau' in r.get('title', '') or 'Zusammenfassung' in r.get('title', ''):
                            key = "sportschau"
                        else:
                            key = f"video_{len(results)}"
                        
                        results[key] = {
                            'video_id': video_id,
                            'url': url,
                            'title': r.get('title', ''),
                            'query': query
                        }
                        break  # Nur erstes Video pro Query
        except Exception as e:
            print(f"Error searching '{query}': {e}")
    
    return results

def get_videos_for_match(team1_key, team2_key, teams_config):
    """Holt Videos für ein Spiel basierend auf Team-Namen"""
    team1 = teams_config[team1_key]['name']
    team2 = teams_config[team2_key]['name']
    
    return search_videos(team1, team2)

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config.teams import TEAMS
    
    if len(sys.argv) > 2:
        team1 = sys.argv[1]
        team2 = sys.argv[2]
    else:
        team1 = 'st_pauli'
        team2 = 'werder'
    
    print(f"🔍 Suche Videos für: {TEAMS[team1]['name']} vs {TEAMS[team2]['name']}")
    print("=" * 50)
    
    videos = get_videos_for_match(team1, team2, TEAMS)
    
    if videos:
        print(f"\n✅ {len(videos)} Videos gefunden:\n")
        for key, vid in videos.items():
            print(f"  [{key}]")
            print(f"    Title: {vid['title']}")
            print(f"    URL: https://youtube.com/watch?v={vid['video_id']}")
            print()
    else:
        print("❌ Keine Videos gefunden")
