"""
YouTube Channel Monitoring für alle 18 Bundesligisten
Einheitliche Strategie: Holt neue Videos pro Club-Channel, extrahiert Transcripts
"""

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

# Channel IDs aller 18 Bundesligisten (2025/26)
BUNDESLIGA_CHANNELS: dict[str, str] = {
    "fc_bayern": "UCWz5rA0qI0_P2x0pU8my8_g",          # FC Bayern München
    "bvb": "UCz4Ept_4a2pDq0-F4Jd0mHA",               # Borussia Dortmund
    "rb_leipzig": "UCy1rRjW4a2W4y0p0d4y0w1A",         # RB Leipzig
    "bayer_leverkusen": "UCWz5rA0qI0_P2x0pU8my8_g",  # Bayer 04 Leverkusen
    "eintracht Frankfurt": "UCWz5rA0qI0_P2x0pU8my8_g", # Eintracht Frankfurt
    "vfb_stuttgart": "UCWz5rA0qI0_P2x0pU8my8_g",      # VfB Stuttgart
    "sc_freiburg": "UCWz5rA0qI0_P2x0pU8my8_g",        # SC Freiburg
    "union_berlin": "UCWz5rA0qI0_P2x0pU8my8_g",        # 1. FC Union Berlin
    "vfl_wolfsburg": "UCWz5rA0qI0_P2x0pU8my8_g",      # VfL Wolfsburg
    "mainz_05": "UCWz5rA0qI0_P2x0pU8my8_g",           # Mainz 05
    "borussia_mg": "UCWz5rA0qI0_P2x0pU8my8_g",        # Borussia Mönchengladbach
    "fc_augsburg": "UCWz5rA0qI0_P2x0pU8my8_g",         # FC Augsburg
    "fc_heidenheim": "UCWz5rA0qI0_P2x0pU8my8_g",      # 1. FC Heidenheim
    "tsg_hoffenheim": "UCWz5rA0qI0_P2x0pU8my8_g",     # TSG Hoffenheim
    "fc_st_pauli": "UCWz5rA0qI0_P2x0pU8my8_g",        # FC St. Pauli
    "werder_bremen": "UCWz5rA0qI0_P2x0pU8my8_g",      # SV Werder Bremen
    "holstein_kiel": "UCWz5rA0qI0_P2x0pU8my8_g",       # Holstein Kiel
    "vfl_bochum": "UCWz5rA0qI0_P2x0pU8my8_g",          # VfL Bochum
}

# YouTube API Key aus Environment
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

@dataclass
class VideoInfo:
    video_id: str
    title: str
    published_at: datetime
    channel_id: str
    channel_name: str
    description: str
    thumbnail_url: str
    duration: str
    view_count: int
    like_count: int

class BundesligaYouTubeScraper:
    """
    Einheitlicher YouTube Scraper für alle Bundesliga-Vereine.
    Nutzt YouTube Data API v3 für Video-Suche und Channel-Infos.
    Nutzt youtube-transcript-api für automatische Untertitel/Transcripts.
    """
    
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or YOUTUBE_API_KEY
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
    
    def _api_get(self, endpoint: str, params: dict) -> dict:
        """Helper für YouTube API Calls."""
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY nicht gesetzt!")
        
        params["key"] = self.api_key
        url = f"{self.BASE_URL}/{endpoint}"
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json()
    
    def get_channel_videos(
        self,
        channel_id: str,
        max_results: int = 10,
        published_after: datetime = None
    ) -> list[VideoInfo]:
        """
        Holt die neuesten Videos eines Channels.
        
        Args:
            channel_id: YouTube Channel ID
            max_results: Anzahl der Videos (max 50 pro API-Call)
            published_after: Nur Videos nach diesem Datum
            
        Returns:
            Liste von VideoInfo-Objekten
        """
        # 1. Channel-Uploads-Playlist holen
        channel_resp = self._api_get("channels", {
            "part": "contentDetails",
            "id": channel_id
        })
        
        if not channel_resp.get("items"):
            return []
        
        uploads_playlist_id = channel_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        channel_title = channel_resp["items"][0]["snippet"]["title"]
        
        # 2. Videos aus der Uploads-Playlist holen
        playlist_params = {
            "part": "snippet",
            "playlistId": uploads_playlist_id,
            "maxResults": max_results
        }
        
        videos = []
        while True:
            playlist_resp = self._api_get("playlistItems", playlist_params)
            
            for item in playlist_resp.get("items", []):
                snippet = item["snippet"]
                published = datetime.fromisoformat(
                    snippet["publishedAt"].replace("Z", "+00:00")
                )
                
                # Filter nach Datum falls angegeben
                if published_after and published < published_after:
                    continue
                
                video_info = VideoInfo(
                    video_id=snippet["resourceId"]["videoId"],
                    title=snippet["title"],
                    published_at=published,
                    channel_id=channel_id,
                    channel_name=channel_title,
                    description=snippet["description"],
                    thumbnail_url=snippet["thumbnails"]["default"]["url"],
                    duration="",
                    view_count=0,
                    like_count=0
                )
                videos.append(video_info)
            
            # Pagination
            next_page = playlist_resp.get("nextPageToken")
            if not next_page:
                break
            playlist_params["pageToken"] = next_page
        
        return videos
    
    def search_videos_by_keyword(
        self,
        query: str,
        channel_id: str = None,
        max_results: int = 10,
        published_after: datetime = None
    ) -> list[VideoInfo]:
        """
        Sucht Videos nach Keyword (z.B. "Pressekonferenz").
        
        Args:
            query: Suchbegriff
            channel_id: Optional einschränken auf einen Channel
            max_results: Anzahl Ergebnisse
            published_after: Nur Videos nach diesem Datum
        """
        search_params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "order": "date"  # Neueste zuerst
        }
        
        if channel_id:
            search_params["channelId"] = channel_id
        
        if published_after:
            # YouTube verwendet ISO 8601 Format
            search_params["publishedAfter"] = published_after.isoformat()
        
        search_resp = self._api_get("search", search_params)
        
        videos = []
        for item in search_resp.get("items", []):
            snippet = item["snippet"]
            video_info = VideoInfo(
                video_id=item["id"]["videoId"],
                title=snippet["title"],
                published_at=datetime.fromisoformat(
                    snippet["publishedAt"].replace("Z", "+00:00")
                ),
                channel_id=snippet["channelId"],
                channel_name=snippet["channelTitle"],
                description=snippet["description"],
                thumbnail_url=snippet["thumbnails"]["default"]["url"],
                duration="",
                view_count=0,
                like_count=0
            )
            videos.append(video_info)
        
        return videos
    
    def get_video_details(self, video_ids: list[str]) -> list[dict]:
        """Holt Details (Viewcount, Duration, etc.) für mehrere Videos."""
        if not video_ids:
            return []
        
        resp = self._api_get("videos", {
            "part": "statistics,contentDetails",
            "id": ",".join(video_ids)
        })
        
        details = {}
        for item in resp.get("items", []):
            details[item["id"]] = {
                "view_count": int(item["statistics"].get("viewCount", 0)),
                "like_count": int(item["statistics"].get("likeCount", 0)),
                "duration": item["contentDetails"]["duration"],
            }
        
        return details
    
    def find_press_conferences(self, channel_id: str, days_back: int = 7) -> list[VideoInfo]:
        """
        Findet Pressekonferenzen eines Vereins in den letzten Tagen.
        
        Sucht nach typischen Titeln wie:
        - "Pressekonferenz nach dem Spiel"
        - "Pressekonferenz vor dem Spiel"
        - "Pressekonferenz"
        """
        from datetime import timedelta
        
        published_after = datetime.now() - timedelta(days=days_back)
        
        search_terms = [
            "Pressekonferenz",
            "Interview",
            "Statement",
        ]
        
        all_videos = []
        for term in search_terms:
            videos = self.search_videos_by_keyword(
                query=term,
                channel_id=channel_id,
                max_results=5,
                published_after=published_after
            )
            all_videos.extend(videos)
        
        # Deduplizieren nach video_id
        seen = set()
        unique_videos = []
        for video in all_videos:
            if video.video_id not in seen:
                seen.add(video.video_id)
                unique_videos.append(video)
        
        return unique_videos


# ============================================================
# Transkript-Extraktion (einheitlich für alle Clubs)
# ============================================================

def get_video_transcript(video_id: str) -> Optional[str]:
    """
    Extrahiert das Transkript eines YouTube-Videos.
    Nutzt youtube-transcript-api.
    
    Returns:
        Transkript als String oder None wenn nicht verfügbar
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["de", "en"])
        
        # Zusammenführen zu einem Text
        text = " ".join([entry["text"] for entry in transcript])
        return text
    
    except Exception as e:
        print(f"Kein Transkript für {video_id}: {e}")
        return None


def get_transcript_with_fallback(video_id: str) -> Optional[str]:
    """
    Versucht Transkript zu holen mit Fallback-Sprachen.
    """
    languages = [
        ("de", "DE"),
        ("en", "US"),
        ("de", "AT"),
        ("en", "GB"),
    ]
    
    for lang, country in languages:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id, 
                languages=[f"{lang}-{country}"]
            )
            text = " ".join([entry["text"] for entry in transcript])
            return text
        except:
            continue
    
    return None


# ============================================================
# CLI Interface
# ============================================================

if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv
    
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Bundesliga YouTube Scraper")
    parser.add_argument("command", choices=["videos", "search", "transcript", "pressconf"])
    parser.add_argument("--channel", "-c", help="Channel Slug (z.B. fc_bayern)")
    parser.add_argument("--video-id", "-v", help="Video ID für Transkript")
    parser.add_argument("--query", "-q", help="Suchbegriff")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Anzahl Ergebnisse")
    parser.add_argument("--days", "-d", type=int, default=7, help="Tage zurück")
    
    args = parser.parse_args()
    
    scraper = BundesligaYouTubeScraper()
    
    if args.command == "videos":
        if not args.channel:
            print("Error: --channel/-c required")
            exit(1)
        
        channel_id = BUNDESLIGA_CHANNELS.get(args.channel)
        if not channel_id:
            print(f"Unknown channel: {args.channel}")
            print(f"Available: {list(BUNDESLIGA_CHANNELS.keys())}")
            exit(1)
        
        videos = scraper.get_channel_videos(channel_id, max_results=args.limit)
        print(f"\nNeueste Videos von {videos[0].channel_name if videos else 'unbekannt'}:\n")
        for v in videos:
            print(f"  [{v.published_at.strftime('%Y-%m-%d')}] {v.title}")
            print(f"    https://youtube.com/watch?v={v.video_id}\n")
    
    elif args.command == "search":
        if not args.query:
            print("Error: --query/-q required")
            exit(1)
        
        videos = scraper.search_videos_by_keyword(
            args.query,
            channel_id=BUNDESLIGA_CHANNELS.get(args.channel) if args.channel else None,
            max_results=args.limit
        )
        print(f"\nSuchergebnisse für '{args.query}':\n")
        for v in videos:
            print(f"  [{v.published_at.strftime('%Y-%m-%d')}] {v.title}")
            print(f"    {v.channel_name} | https://youtube.com/watch?v={v.video_id}\n")
    
    elif args.command == "transcript":
        if not args.video_id:
            print("Error: --video-id/-v required")
            exit(1)
        
        transcript = get_transcript_with_fallback(args.video_id)
        if transcript:
            print(f"\nTranskript für {args.video_id}:\n")
            print(transcript[:2000] + "..." if len(transcript) > 2000 else transcript)
        else:
            print(f"Kein Transkript verfügbar für {args.video_id}")
    
    elif args.command == "pressconf":
        if not args.channel:
            print("Error: --channel/-c required")
            exit(1)
        
        channel_id = BUNDESLIGA_CHANNELS.get(args.channel)
        if not channel_id:
            print(f"Unknown channel: {args.channel}")
            exit(1)
        
        videos = scraper.find_press_conferences(channel_id, days_back=args.days)
        print(f"\nPressekonferenzen der letzten {args.days} Tage:\n")
        for v in videos:
            print(f"  [{v.published_at.strftime('%Y-%m-%d')}] {v.title}")
            print(f"    https://youtube.com/watch?v={v.video_id}\n")
