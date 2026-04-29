"""
Unit Tests für den Bundesliga YouTube Scraper
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from bundesliga_news.src.youtube.scraper import (
    BundesligaYouTubeScraper,
    VideoInfo,
    BUNDESLIGA_CHANNELS,
    get_video_transcript,
)


class TestBundesligaChannels:
    """Tests für die Channel-Konfiguration."""
    
    def test_all_18_clubs_present(self):
        """Alle 18 Bundesligisten sollten vorhanden sein."""
        assert len(BUNDESLIGA_CHANNELS) == 18
    
    def test_required_clubs_present(self):
        """Wichtige Clubs sollten definitiv vorhanden sein."""
        required = ["fc_bayern", "bvb", "fc_st_pauli", "werder_bremen"]
        for club in required:
            assert club in BUNDESLIGA_CHANNELS, f"Missing club: {club}"


class TestVideoInfo:
    """Tests für das VideoInfo Dataclass."""
    
    def test_video_info_creation(self):
        video = VideoInfo(
            video_id="abc123",
            title="Test Video",
            published_at=datetime.now(),
            channel_id="UCWz5rA0qI0_P2x0pU8my8_g",
            channel_name="FC Bayern",
            description="Test description",
            thumbnail_url="https://example.com/thumb.jpg",
            duration="PT5M30S",
            view_count=1000,
            like_count=50
        )
        
        assert video.video_id == "abc123"
        assert video.title == "Test Video"
        assert video.view_count == 1000


class TestBundesligaYouTubeScraper:
    """Tests für den YouTube Scraper."""
    
    @patch("bundesliga_news.src.youtube.scraper.requests.Session")
    def test_api_get_builds_correct_url(self, mock_session):
        """API Calls sollten die korrekte URL bauen."""
        mock_resp = Mock()
        mock_resp.json.return_value = {"items": []}
        mock_session.return_value.get.return_value = mock_resp
        
        scraper = BundesligaYouTubeScraper(api_key="test_key_123")
        scraper.session = mock_session.return_value
        
        # Direkt testen
        scraper.session.get = mock.Mock(return_value=mock_resp)
        
        result = scraper._api_get("channels", {"part": "snippet", "id": "test"})
        
        scraper.session.get.assert_called_once()
        call_args = scraper.session.get.call_args
        assert "channels" in call_args[0][0]
        assert call_args[1]["params"]["key"] == "test_key_123"
    
    @patch("bundesliga_news.src.youtube.scraper.requests.get")
    def test_get_channel_videos_returns_list(self, mock_get):
        """get_channel_videos sollte eine Liste zurückgeben."""
        mock_resp = Mock()
        mock_resp.json.return_value = {
            "items": [{
                "contentDetails": {"relatedPlaylists": {"uploads": "UUWz5rA0qI0"}},
                "snippet": {"title": "FC Bayern"}
            }]
        }
        mock_get.return_value = mock_resp
        
        scraper = BundesligaYouTubeScraper(api_key="test_key")
        
        # Mock playlistItems response
        with patch.object(scraper, "_api_get") as mock_api:
            mock_api.return_value = {
                "items": [{
                    "snippet": {
                        "resourceId": {"videoId": "vid123"},
                        "title": "Pressekonferenz",
                        "publishedAt": "2026-04-28T10:00:00Z",
                        "thumbnails": {"default": {"url": "https://example.com/thumb.jpg"}},
                        "description": "Test"
                    }
                }]
            }
            
            videos = scraper.get_channel_videos("UCWz5rA0qI0_P2x0pU8my8_g")
            
            assert len(videos) == 1
            assert videos[0].video_id == "vid123"
            assert videos[0].channel_name == "FC Bayern"


class TestTranscriptExtraction:
    """Tests für die Transkript-Extraktion."""
    
    def test_get_transcript_handles_exception(self):
        """Fehler beim Transkript-Holen sollten abgefangen werden."""
        with patch("bundesliga_news.src.youtube.scraper.YouTubeTranscriptApi.get_transcript") as mock_transcript:
            mock_transcript.side_effect = Exception("Transkript nicht verfügbar")
            
            result = get_video_transcript("invalid_video_id")
            
            assert result is None
    
    def test_get_transcript_success(self):
        """Erfolgreiche Transkript-Extraktion."""
        with patch("bundesliga_news.src.youtube.scraper.YouTubeTranscriptApi.get_transcript") as mock_transcript:
            mock_transcript.return_value = [
                {"text": "Hallo"},
                {"text": "Welt"},
                {"text": "das"},
                {"text": "ist"},
                {"text": "ein"},
                {"text": "Test"}
            ]
            
            result = get_video_transcript("valid_video_id")
            
            assert result == "Hallo Welt das ist ein Test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
