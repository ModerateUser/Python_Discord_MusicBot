"""
Enhanced Audio Service with Type Hints, Thread Pool, and Caching
REFACTORED VERSION - Phase 2

Improvements:
- Comprehensive type hints throughout
- Dedicated thread pool for yt-dlp operations
- Integrated caching for metadata and search results
- Better error handling and logging
- Performance optimizations
"""
import discord
import yt_dlp
import asyncio
import logging
import shutil
import os
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

# Import caching utilities
from utils.cache import cached, YOUTUBE_CACHE_CONFIG, SEARCH_CACHE_CONFIG

logger = logging.getLogger('discord_bot')

# Timeout constants
YTDL_TIMEOUT = 30  # seconds
SEARCH_TIMEOUT = 20  # seconds
THREAD_POOL_SIZE = 4  # Dedicated workers for yt-dlp


class AudioServiceError(Exception):
    """Custom exception for audio service errors"""
    pass


@dataclass
class VideoMetadata:
    """Structured video metadata"""
    title: str
    url: str
    webpage_url: str
    duration: int
    uploader: str
    thumbnail: Optional[str] = None
    description: Optional[str] = None
    view_count: Optional[int] = None
    
    @classmethod
    def from_ytdl_data(cls, data: Dict[str, Any]) -> 'VideoMetadata':
        """Create metadata from yt-dlp data"""
        return cls(
            title=data.get('title', 'Unknown'),
            url=data.get('url', ''),
            webpage_url=data.get('webpage_url', ''),
            duration=data.get('duration', 0),
            uploader=data.get('uploader', 'Unknown'),
            thumbnail=data.get('thumbnail'),
            description=data.get('description'),
            view_count=data.get('view_count')
        )


class AudioService:
    """
    Enhanced audio streaming and playback service
    
    Features:
    - Dedicated thread pool for blocking operations
    - Caching for metadata and search results
    - Comprehensive type hints
    - Better error handling
    """
    
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
        'age_limit': None,
        'geo_bypass': True,
        'socket_timeout': 10,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
            'preferredquality': '128',
        }],
    }
    
    # Enhanced FFmpeg options for clean audio
    FFMPEG_OPTIONS = {
        'before_options': (
            '-reconnect 1 '
            '-reconnect_streamed 1 '
            '-reconnect_delay_max 5 '
            '-nostdin'
        ),
        'options': (
            '-vn '
            '-ar 48000 '  # 48kHz sample rate (Discord standard)
            '-ac 2 '  # Stereo output
            '-b:a 128k '  # Consistent bitrate
            '-bufsize 512k '  # Larger buffer
            '-filter:a "volume=1.0,aresample=48000:async=1:first_pts=0" '
            '-loglevel warning'
        )
    }
    
    FFMPEG_OPTIONS_LOCAL = {
        'before_options': '-nostdin',
        'options': (
            '-vn '
            '-ar 48000 '
            '-ac 2 '
            '-b:a 128k '
            '-bufsize 512k '
            '-filter:a "volume=1.0,aresample=48000:async=1:first_pts=0,apad=pad_dur=0.1" '
            '-loglevel warning'
        )
    }
    
    def __init__(self, thread_pool_size: int = THREAD_POOL_SIZE):
        """
        Initialize audio service
        
        Args:
            thread_pool_size: Number of worker threads for yt-dlp operations
        """
        self.ytdl = yt_dlp.YoutubeDL(self.YTDL_OPTIONS)
        self.ffmpeg_path: Optional[str] = self._find_ffmpeg()
        self._ffmpeg_validated: bool = False
        
        # Dedicated thread pool for blocking operations
        self._executor = ThreadPoolExecutor(
            max_workers=thread_pool_size,
            thread_name_prefix="ytdl_worker"
        )
        
        logger.info(f"AudioService initialized with {thread_pool_size} worker threads")
        
        # Validate FFmpeg on initialization
        if not self.ffmpeg_path:
            logger.error(
                "FFmpeg not found in PATH or common locations.\n"
                "Audio playback will not work. Please install FFmpeg:\n"
                "  - Windows: Download from https://ffmpeg.org/download.html\n"
                "  - Linux: sudo apt install ffmpeg\n"
                "  - macOS: brew install ffmpeg"
            )
        else:
            self._validate_ffmpeg()
    
    def _find_ffmpeg(self) -> Optional[str]:
        """
        Find FFmpeg executable in system PATH
        
        Returns:
            Path to FFmpeg executable or None if not found
        """
        # Try system PATH first
        ffmpeg = shutil.which('ffmpeg')
        if ffmpeg:
            logger.info(f"FFmpeg found in PATH: {ffmpeg}")
            return ffmpeg
        
        # Try common Windows locations
        if os.name == 'nt':
            common_paths = [
                r'C:\ffmpeg\bin\ffmpeg.exe',
                r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
                r'C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe',
                os.path.expanduser(r'~\ffmpeg\bin\ffmpeg.exe'),
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    logger.info(f"FFmpeg found at: {path}")
                    return path
        
        # Try common Unix locations
        else:
            common_paths = [
                '/usr/bin/ffmpeg',
                '/usr/local/bin/ffmpeg',
                '/opt/ffmpeg/bin/ffmpeg',
                os.path.expanduser('~/bin/ffmpeg'),
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    logger.info(f"FFmpeg found at: {path}")
                    return path
        
        logger.warning("FFmpeg not found in PATH or common locations")
        return None
    
    def _validate_ffmpeg(self) -> bool:
        """
        Validate that FFmpeg is executable and working
        
        Returns:
            True if FFmpeg is valid, False otherwise
        """
        if not self.ffmpeg_path:
            return False
        
        try:
            ffmpeg_file = Path(self.ffmpeg_path)
            if not ffmpeg_file.exists():
                logger.error(f"FFmpeg path does not exist: {self.ffmpeg_path}")
                return False
            
            if not os.access(self.ffmpeg_path, os.X_OK):
                logger.error(f"FFmpeg is not executable: {self.ffmpeg_path}")
                return False
            
            import subprocess
            result = subprocess.run(
                [self.ffmpeg_path, '-version'],
                capture_output=True,
                timeout=5,
                text=True
            )
            
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0] if result.stdout else "Unknown version"
                logger.info(f"FFmpeg validated successfully: {version_line}")
                self._ffmpeg_validated = True
                return True
            else:
                logger.error(f"FFmpeg validation failed with return code {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg validation timed out")
            return False
        except Exception as e:
            logger.error(f"Error validating FFmpeg: {e}", exc_info=True)
            return False
    
    def is_ffmpeg_available(self) -> bool:
        """
        Check if FFmpeg is available and validated
        
        Returns:
            True if FFmpeg is ready to use
        """
        return self.ffmpeg_path is not None and self._ffmpeg_validated
    
    @cached(**YOUTUBE_CACHE_CONFIG)
    async def get_video_metadata(self, url: str) -> Optional[VideoMetadata]:
        """
        Get video metadata with caching
        
        Args:
            url: YouTube URL
            
        Returns:
            VideoMetadata object or None on failure
        """
        loop = asyncio.get_event_loop()
        
        try:
            data = await asyncio.wait_for(
                loop.run_in_executor(
                    self._executor,  # Use dedicated thread pool
                    lambda: self.ytdl.extract_info(url, download=False)
                ),
                timeout=YTDL_TIMEOUT
            )
            
            if not data:
                return None
            
            # Handle playlists
            if 'entries' in data:
                if not data['entries']:
                    return None
                data = data['entries'][0]
            
            return VideoMetadata.from_ytdl_data(data)
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout getting metadata for: {url}")
            return None
        except Exception as e:
            logger.error(f"Error getting metadata for {url}: {e}", exc_info=True)
            return None
    
    async def create_ytdl_source(
        self, 
        url: str, 
        *, 
        loop: Optional[asyncio.AbstractEventLoop] = None, 
        stream: bool = True
    ) -> Optional['YTDLSource']:
        """
        Create a YTDLSource from URL
        
        Args:
            url: YouTube URL or search query
            loop: Event loop to use
            stream: Whether to stream or download
            
        Returns:
            YTDLSource object or None on failure
        """
        if not self.is_ffmpeg_available():
            logger.error("Cannot create audio source: FFmpeg is not available")
            return None
        
        loop = loop or asyncio.get_event_loop()
        
        try:
            # Use dedicated thread pool for yt-dlp operation
            data = await asyncio.wait_for(
                loop.run_in_executor(
                    self._executor,  # Dedicated thread pool
                    lambda: self.ytdl.extract_info(url, download=not stream)
                ),
                timeout=YTDL_TIMEOUT
            )
            
            if not data:
                logger.error(f"No data extracted from URL: {url}")
                return None
            
            # Handle playlists
            if 'entries' in data:
                if not data['entries']:
                    logger.error(f"Empty playlist or no entries: {url}")
                    return None
                data = data['entries'][0]
            
            # Get the stream URL
            if stream:
                if 'url' not in data:
                    logger.error(f"No stream URL found in data for: {url}")
                    return None
                filename = data['url']
            else:
                filename = self.ytdl.prepare_filename(data)
            
            # Create FFmpeg audio source
            ffmpeg_options = self.FFMPEG_OPTIONS.copy()
            
            logger.debug(f"Creating audio source for: {data.get('title', 'Unknown')}")
            
            audio_source = discord.FFmpegPCMAudio(
                filename, 
                executable=self.ffmpeg_path,
                **ffmpeg_options
            )
            
            return YTDLSource(audio_source, data=data)
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout extracting info from URL (>{YTDL_TIMEOUT}s): {url}")
            return None
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"yt-dlp download error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating YTDL source for {url}: {e}", exc_info=True)
            return None
    
    @cached(**SEARCH_CACHE_CONFIG)
    async def search_youtube(
        self, 
        query: str, 
        max_results: int = 5
    ) -> Optional[List[VideoMetadata]]:
        """
        Search YouTube with caching
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of VideoMetadata objects or None on failure
        """
        search_query = f"ytsearch{max_results}:{query}"
        loop = asyncio.get_event_loop()
        
        try:
            info = await asyncio.wait_for(
                loop.run_in_executor(
                    self._executor,  # Use dedicated thread pool
                    lambda: self.ytdl.extract_info(search_query, download=False)
                ),
                timeout=SEARCH_TIMEOUT
            )
            
            if 'entries' in info and info['entries']:
                results = []
                for entry in info['entries'][:max_results]:
                    try:
                        metadata = VideoMetadata.from_ytdl_data(entry)
                        results.append(metadata)
                    except Exception as e:
                        logger.warning(f"Error parsing search result: {e}")
                        continue
                
                return results if results else None
            
            logger.warning(f"No search results for: {query}")
            return None
        
        except asyncio.TimeoutError:
            logger.error(f"Search timeout (>{SEARCH_TIMEOUT}s) for query: {query}")
            return None
        except Exception as e:
            logger.error(f"Search error for '{query}': {e}", exc_info=True)
            return None
    
    def create_local_source(
        self, 
        filepath: Union[str, Path]
    ) -> Optional[discord.FFmpegPCMAudio]:
        """
        Create an audio source from local file
        
        Args:
            filepath: Path to local audio file
            
        Returns:
            FFmpegPCMAudio source or None on failure
        """
        if not self.is_ffmpeg_available():
            logger.error("Cannot create local source: FFmpeg is not available")
            return None
        
        filepath = Path(filepath)
        
        # Validate file exists
        if not filepath.exists():
            logger.error(f"Local file does not exist: {filepath}")
            return None
        
        # Validate file is readable
        if not os.access(filepath, os.R_OK):
            logger.error(f"Local file is not readable: {filepath}")
            return None
        
        try:
            ffmpeg_options = self.FFMPEG_OPTIONS_LOCAL.copy()
            
            logger.debug(f"Creating local audio source for: {filepath}")
            
            return discord.FFmpegPCMAudio(
                str(filepath),
                executable=self.ffmpeg_path,
                **ffmpeg_options
            )
                
        except Exception as e:
            logger.error(f"Error creating local source for {filepath}: {e}", exc_info=True)
            return None
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the audio service"""
        logger.info("Shutting down AudioService...")
        
        # Shutdown thread pool
        self._executor.shutdown(wait=True, cancel_futures=True)
        
        logger.info("AudioService shutdown complete")
    
    def __del__(self):
        """Cleanup on deletion"""
        try:
            self._executor.shutdown(wait=False, cancel_futures=True)
        except:
            pass


class YTDLSource(discord.PCMVolumeTransformer):
    """
    YouTube audio source with volume control
    """
    
    def __init__(
        self, 
        source: discord.AudioSource, 
        *, 
        data: Dict[str, Any], 
        volume: float = 0.5
    ):
        """
        Initialize YTDL source
        
        Args:
            source: Audio source
            data: yt-dlp data dictionary
            volume: Initial volume (0.0 to 2.0)
        """
        super().__init__(source, volume)
        self.data: Dict[str, Any] = data
        self.title: str = data.get('title', 'Unknown')
        self.url: str = data.get('url', '')
        self.webpage_url: str = data.get('webpage_url', '')
        self.duration: int = data.get('duration', 0)
        self.uploader: str = data.get('uploader', 'Unknown')
        self._last_volume: float = volume
    
    def __repr__(self) -> str:
        return f"YTDLSource(title='{self.title}', duration={self.duration})"
    
    @property
    def volume(self) -> float:
        """Get current volume"""
        return self._volume
    
    @volume.setter
    def volume(self, value: float) -> None:
        """
        Set volume with validation
        
        Args:
            value: Volume level (0.0 to 2.0)
        """
        # Clamp volume between 0.0 and 2.0
        value = max(0.0, min(2.0, value))
        
        # Log significant volume changes
        if abs(value - self._last_volume) > 0.3:
            logger.debug(f"Large volume change: {self._last_volume:.2f} -> {value:.2f}")
        
        self._volume = value
        self._last_volume = value
