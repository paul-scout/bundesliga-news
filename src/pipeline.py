#!/usr/bin/env python3
"""
Main Pipeline: Bundesliga News Automator
"""
from transcripts.get_transcript import get_transcript
from scrapers.find_videos import get_preset_videos
import json
import os

def run_pipeline(match_name):
    """Führt die komplette Pipeline aus"""
    print(f"\n🏆 Bundesliga News Pipeline: {match_name}\n")
    print("=" * 50)
    
    # 1. Videos finden
    print("\n1️⃣ Videos suchen...")
    videos = get_preset_videos(match_name)
    for name, vid in videos.items():
        print(f"   {name}: {vid}")
    
    # 2. Transcripts extrahieren
    print("\n2️⃣ Transcripts extrahieren...")
    transcripts = {}
    for name, vid in videos.items():
        print(f"   Extrahiere: {name}...")
        try:
            transcripts[name] = get_transcript(vid)
            print(f"   ✅ {len(transcripts[name])} Zeichen")
        except Exception as e:
            print(f"   ❌ Fehler: {e}")
    
    # 3. Speichern
    print("\n3️⃣ Speichern...")
    os.makedirs('data', exist_ok=True)
    with open(f'data/{match_name}_transcripts.json', 'w') as f:
        json.dump(transcripts, f, indent=2)
    print(f"   ✅ Gespeichert: data/{match_name}_transcripts.json")
    
    # 4. Nächster Schritt: LLM Artikel
    print("\n4️⃣ Nächster Schritt:")
    print("   → LLM für Artikelgenerierung nutzen")
    
    print("\n" + "=" * 50)
    print("✅ Pipeline abgeschlossen!")
    
    return transcripts

if __name__ == "__main__":
    import sys
    match = sys.argv[1] if len(sys.argv) > 1 else 'st_pauli_werder'
    run_pipeline(match)
