"""
Audio streaming and playback service
Handles YouTube downloads and audio source creation with error handling
"""
import discord
import yt_dlp
import asyncio
from typing import Optional
import logging
import time
from collections import deque

logger = logging.getLogger('discord_bot')


class AudioService:
    """Handles audio streaming and source creation with rate limiting"""
    
    # yt-dlp options
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
        'extract_flat': False,
        'socket_timeout': 30,
        'retries': 3,
    }
    
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }
    
    def __init__(self):
        self.ytdl = yt_dlp.YoutubeDL(self.YTDL_OPTIONS)
        
        # Rate limiting: track last 10 requests
        self._request_times = deque(maxlen=10)
        self._rate_limit_window = 60  # seconds
        self._max_requests_per_window = 10
    
    def _check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits
        Returns True if request is allowed, False if rate limited
        """
        now = time.time()
        
        # Remove old requests outside the window
        while self._request_times and now - self._request_times[0] > self._rate_limit_window:
            self._request_times.popleft()
        
        # Check if we've hit the limit
        if len(self._request_times) >= self._max_requests_per_window:
            logger.warning("Rate limit reached for audio service")
            return False
        
        # Record this request
        self._request_times.append(now)
        return True
    
    async def create_ytdl_source(self, url: str, *, loop=None, stream: bool = True) -> Optional['YTDLSource']:
        """
        Create a YTDLSource from URL with error handling
        Returns YTDLSource or None on failure
        """
        # Check rate limit
        if not self._check_rate_limit():
            logger.warning(f"Rate limited, rejecting request for: {url}")
            return None
        
        loop = loop or asyncio.get_event_loop()
        
        try:
            data = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self._extract_info(url, download=not stream)
                ),
                timeout=45.0  # 45 second timeout
            )
            
            if not data:
                logger.warning(f"No data extracted from URL: {url}")
                return None
            
            # Handle playlist results (take first entry)
            if 'entries' in data:
                if not data['entries']:
                    logger.warning(f"Empty playlist/search result for: {url}")
                    return None
                data = data['entries'][0]
            
            # Validate required fields
            if not data.get('url') and not data.get('webpage_url'):
                logger.error(f"No playable URL in extracted data for: {url}")
                return None
            
            filename = data['url'] if stream else self.ytdl.prepare_filename(data)
            
            # Create audio source with error handling
            try:
                audio_source = discord.FFmpegPCMAudio(filename, **self.FFMPEG_OPTIONS)
                return YTDLSource(audio_source, data=data)
            except Exception as e:
                logger.error(f"Failed to create FFmpeg audio source: {e}")
                return None
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout extracting info from: {url}")
            return None
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"yt-dlp download error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating YTDL source for {url}: {e}", exc_info=True)
            return None
    
    def _extract_info(self, url: str, download: bool = False) -> Optional[dict]:
        """
        Extract info using yt-dlp with error handling
        Returns dict or None on failure
        """
        try:
            return self.ytdl.extract_info(url, download=download)
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Download error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error extracting info: {e}", exc_info=True)
            return None
    
    async def search_youtube(self, query: str, max_results: int = 5) -> Optional[list]:
        """
        Search YouTube and return results with error handling
        Returns list of results or None on failure
        """
        if not query or len(query) > 100:
            logger.warning(f"Invalid search query length: {len(query) if query else 0}")
            return None
        
        # Check rate limit
        if not self._check_rate_limit():
            logger.warning(f"Rate limited, rejecting search for: {query}")
            return None
        
        # Sanitize max_results
        max_results = max(1, min(max_results, 10))
        
        search_query = f"ytsearch{max_results}:{query}"
        loop = asyncio.get_event_loop()
        
        try:
            info = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self._extract_info(search_query, download=False)
                ),
                timeout=30.0  # 30 second timeout for searches
            )
            
            if not info:
                return None
            
            if 'entries' in info:
                results = info['entries'][:max_results]
                # Filter out None entries (failed extractions)
                results = [r for r in results if r is not None]
                return results if results else None
            
            return None
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout searching for: {query}")
            return None
        except Exception as e:
            logger.error(f"Search error for '{query}': {e}", exc_info=True)
            return None
    
    def create_local_source(self, filepath: str) -> Optional[discord.FFmpegPCMAudio]:
        """
        Create an audio source from local file with error handling
        Returns FFmpegPCMAudio or None on failure
        """
        try:
            # Validate file exists
            import os
            if not os.path.exists(filepath):
                logger.error(f"Local file not found: {filepath}")
                return None
            
            # Validate file is readable
            if not os.access(filepath, os.R_OK):
                logger.error(f"Local file not readable: {filepath}")
                return None
            
            return discord.FFmpegPCMAudio(filepath, **self.FFMPEG_OPTIONS)
            
        except Exception as e:
            logger.error(f"Error creating local audio source for {filepath}: {e}", exc_info=True)
            return None


class YTDLSource(discord.PCMVolumeTransformer):
    """Represents a YouTube audio source with metadata"""
    
    def __init__(self, source: discord.AudioSource, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title', 'Unknown')
        self.url = data.get('url')
        self.webpage_url = data.get('webpage_url')
        self.duration = data.get('duration', 0)
        self.uploader = data.get('uploader', 'Unknown')
        self.thumbnail = data.get('thumbnail')
    
    def __repr__(self) -> str:
        return f"YTDLSource(title='{self.title}', duration={self.duration})"


# Global audio service instance
audio_service = AudioService()
