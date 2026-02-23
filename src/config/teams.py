#!/usr/bin/env python3
"""
Bundesliga Vereine Konfiguration
YouTube Channels für alle 18 Bundesligisten
"""

TEAMS = {
    'bayern': {
        'name': 'FC Bayern München',
        'short': 'Bayern',
        'youtube': '@fcbayern',
    },
    'dortmund': {
        'name': 'Borussia Dortmund',
        'short': 'BVB',
        'youtube': '@BVB',
    },
    'leipzig': {
        'name': 'RB Leipzig',
        'short': 'RBL',
        'youtube': '@RBLeipzig',
    },
    'leverkusen': {
        'name': 'Bayer 04 Leverkusen',
        'short': 'Leverkusen',
        'youtube': '@bayer04',
    },
    'frankfurt': {
        'name': 'Eintracht Frankfurt',
        'short': 'SGE',
        'youtube': '@Eintracht',
    },
    'stuttgart': {
        'name': 'VfB Stuttgart',
        'short': 'VFB',
        'youtube': '@vfbstuttgart',
    },
    'freiburg': {
        'name': 'SC Freiburg',
        'short': 'SCF',
        'youtube': '@SCFreiburg',
    },
    'union': {
        'name': '1. FC Union Berlin',
        'short': 'Union',
        'youtube': '@unionberlin',
    },
    'wolfsburg': {
        'name': 'VfL Wolfsburg',
        'short': 'Wolfsburg',
        'youtube': '@vflwolfsburg',
    },
    'mainz': {
        'name': '1. FSV Mainz 05',
        'short': 'Mainz',
        'youtube': '@mainz05',
    },
    'gladbach': {
        'name': 'Borussia Mönchengladbach',
        'short': 'BMG',
        'youtube': '@borussia',
    },
    'augsburg': {
        'name': 'FC Augsburg',
        'short': 'FCA',
        'youtube': '@fcaugsburg',
    },
    'heidenheim': {
        'name': '1. FC Heidenheim',
        'short': 'FCH',
        'youtube': '@fcheidenheim',
    },
    'hoffenheim': {
        'name': 'TSG 1899 Hoffenheim',
        'short': 'TSG',
        'youtube': '@TSGHoffenheim1899',
    },
    'st_pauli': {
        'name': 'FC St. Pauli',
        'short': 'St. Pauli',
        'youtube': '@fcstpauli',
    },
    'werder': {
        'name': 'SV Werder Bremen',
        'short': 'Werder',
        'youtube': '@werderbremen',
    },
    'kiel': {
        'name': 'Holstein Kiel',
        'short': 'Kiel',
        'youtube': '@holsteinkiel',
    },
    'bochum': {
        'name': 'VfL Bochum',
        'short': 'Bochum',
        'youtube': '@vflbochum',
    },
}

# Such-Strategien für Pressekonferenzen
SEARCH_QUERIES = {
    'presse_vor': '{team} Pressekonferenz vor dem Spiel',
    'presse_nach': '{team} Pressekonferenz nach dem Spiel',
    'stimmen': '{team} Stimmen nach dem Spiel',
    'interview': '{team} Interview Spieler',
    'sportschau': 'Sportschau {team} Zusammenfassung',
}

def get_search_query(match_key, team_key):
    """Erstellt Suchbegriff für ein Team"""
    team = TEAMS[team_key]['name']
    return SEARCH_QUERIES[match_key].format(team=team)

if __name__ == "__main__":
    print("🏆 Bundesliga Teams (18)")
    print("=" * 40)
    for key, data in TEAMS.items():
        print(f"{data['short']:6} -> {data['name']} ({data['youtube']})")
