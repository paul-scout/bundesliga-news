# ⚽ Bundesliga News Automator

Automatische News-Artikel aus Pressekonferenzen & Spielen.

## 🚀 Quick Start

```bash
# Transcripts extrahieren
python3 src/transcripts/get_transcript.py <video_id>

# Artikel generieren
python3 src/articles/generate_article.py

# Pipeline ausführen
python3 src/pipeline.py --match "St. Pauli vs Werder"
```

## 📁 Struktur

```
bundesliga-news/
├── src/
│   ├── transcripts/    # YouTube Transcript Extraktion
│   ├── articles/       # LLM News-Generator
│   ├── scrapers/      # Video-Finder
│   └── pipeline.py    # Hauptskript
├── data/              # Gespeicherte Artikel
└── package.json
```

## 🔧 Tech Stack

- **youtube-transcript-api** — Transcripts von YouTube
- **Tavily** — Recherche
- **LLM** — Artikelgenerierung
- **OpenLigaDB** — Spieldaten

---

*Built by Paul der II. | Februar 2026*
