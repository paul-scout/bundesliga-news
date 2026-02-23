#!/usr/bin/env python3
"""
Bundesliga Video Finder
Findet Pressekonferenzen und Interviews zu einem Spiel
"""
# import requests
# from bs4 import BeautifulSoup

# Bekannte YouTube Channels für Bundesliga
CHANNELS = {
    'st_pauli': '@fcstpauli',
    'werder': '@werderbremen',
    'sportschau': '@sportschau',
    'bild': '@BILD'
}

def search_videos(query, max_results=5):
    """Sucht YouTube Videos (需要有 YouTube Data API)"""
    # TODO: Implementieren mit YouTube API oder Scrape
    pass

def get_preset_videos(match_name):
    """Vordefinierte Videos für Test"""
    videos = {
        'st_pauli_werder': {
            'sportschau': '7sXpB8cYRKo',
            'presse_nach_spiel': 'L8Tf8SchI4I',
            'stimmen_nach_spiel': 'FVYdYlPv9lc',
            'presse_vor_spiel_st_pauli': 'FJduT97k7aM',
        }
    }
    return videos.get(match_name, {})

if __name__ == "__main__":
    import sys
    match = sys.argv[1] if len(sys.argv) > 1 else 'st_pauli_werder'
    videos = get_preset_videos(match)
    
    for name, vid in videos.items():
        print(f"{name}: https://youtube.com/watch?v={vid}")
