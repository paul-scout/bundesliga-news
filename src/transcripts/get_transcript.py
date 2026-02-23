#!/usr/bin/env python3
"""
YouTube Transcript Extractor für Bundesliga Pressekonferenzen
"""
from youtube_transcript_api import YouTubeTranscriptApi
import sys
import json

def get_transcript(video_id, lang='de'):
    """Extrahiert Transcript von YouTube Video"""
    yt = YouTubeTranscriptApi()
    transcript_list = yt.list(video_id)
    
    # Versuche deutsche Transcripts
    try:
        transcript = transcript_list.find_transcript([lang])
    except:
        # Fallback: auto-generated
        transcript = transcript_list.find_transcript(['de'])
    
    data = transcript.fetch()
    return ' '.join([t.text for t in data])

def save_transcript(video_id, filename=None):
    """Speichert Transcript in Datei"""
    text = get_transcript(video_id)
    
    if filename:
        with open(filename, 'w') as f:
            f.write(text)
        print(f"✅ Transcript gespeichert: {filename}")
    else:
        print(text)
    
    return text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_transcript.py <video_id> [output_file]")
        sys.exit(1)
    
    video_id = sys.argv[1]
    filename = sys.argv[2] if len(sys.argv) > 2 else None
    
    save_transcript(video_id, filename)
