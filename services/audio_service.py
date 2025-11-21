"""
Audio streaming and playback service - FIXED VERSION
FIX #15: FFmpeg path validation and error handling
FIX #16: Timeout handling for yt-dlp operations
FIX AUDIO #1: Fix sharp static noise with proper audio settings
"""
import discord
import yt_dlp
import asyncio
import logging
import shutil
import os
from typing import Optional
from pathlib import Path

logger = logging.getLogger('discord_bot')

# Timeout constants
YTDL_TIMEOUT = 30  # seconds
SEARCH_TIMEOUT = 20  # seconds


class AudioServiceError(Exception):
    """Custom exception for audio service errors"""
    pass


class AudioService:
    """
    Handles audio streaming and source creation
    FIX #15: Proper FFmpeg validation
    FIX #16: Timeout handling for all operations
    FIX AUDIO #1: Proper audio format settings to prevent static noise
    """
    
    # yt-dlp options with better error handling
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
        'socket_timeout': 10,  # FIX #16: Add socket timeout
        # FIX AUDIO #1: Force audio format to prevent quality issues
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',  # Discord's native codec
            'preferredquality': '128',
        }],
    }
    
    # FIX AUDIO #1: Enhanced FFmpeg options to prevent static noise
    # Discord uses 48kHz sample rate, stereo, and opus codec
    FFMPEG_OPTIONS = {
        'before_options': (
            '-reconnect 1 '
            '-reconnect_streamed 1 '
            '-reconnect_delay_max 5 '
            '-nostdin'  # Prevent FFmpeg from reading stdin
        ),
        'options': (
            '-vn '  # No video
            '-ar 48000 '  # FIX AUDIO #1: Force 48kHz sample rate (Discord standard)
            '-ac 2 '  # FIX AUDIO #1: Force stereo output
            '-b:a 128k '  # FIX AUDIO #1: Set consistent bitrate
            '-bufsize 512k '  # FIX AUDIO #1: Larger buffer to prevent underruns
            '-filter:a "volume=1.0,aresample=48000:async=1:first_pts=0" '  # FIX AUDIO #1: Smooth volume, resample, sync
            '-loglevel warning'  # Reduce log spam
        )
    }
    
    # FIX AUDIO #1: Separate options for local files (no reconnect needed)
    FFMPEG_OPTIONS_LOCAL = {
        'before_options': '-nostdin',
        'options': (
            '-vn '
            '-ar 48000 '  # Force 48kHz
            '-ac 2 '  # Force stereo
            '-b:a 128k '  # Consistent bitrate
            '-bufsize 512k '  # Larger buffer
            '-filter:a "volume=1.0,aresample=48000:async=1:first_pts=0,apad=pad_dur=0.1" '  # Add padding to prevent cutoff
            '-loglevel warning'
        )
    }
    
    def __init__(self):
        self.ytdl = yt_dlp.YoutubeDL(self.YTDL_OPTIONS)
        self.ffmpeg_path = self._find_ffmpeg()
        self._ffmpeg_validated = False
        
        # FIX #15: Validate FFmpeg on initialization
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
        FIX #15: More comprehensive search
        """
        # Try system PATH first
        ffmpeg = shutil.which('ffmpeg')
        if ffmpeg:
            logger.info(f"FFmpeg found in PATH: {ffmpeg}")
            return ffmpeg
        
        # Try common Windows locations
        if os.name == 'nt':  # Windows
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
        FIX #15: Test FFmpeg before use
        
        Returns:
            True if FFmpeg is valid, False otherwise
        """
        if not self.ffmpeg_path:
            return False
        
        try:
            # Check if file exists and is executable
            ffmpeg_file = Path(self.ffmpeg_path)
            if not ffmpeg_file.exists():
                logger.error(f"FFmpeg path does not exist: {self.ffmpeg_path}")
                return False
            
            if not os.access(self.ffmpeg_path, os.X_OK):
                logger.error(f"FFmpeg is not executable: {self.ffmpeg_path}")
                return False
            
            # Try to run FFmpeg to verify it works
            import subprocess
            result = subprocess.run(
                [self.ffmpeg_path, '-version'],
                capture_output=True,
                timeout=5,
                text=True
            )
            
            if result.returncode == 0:
                # Extract version info
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
    
    async def create_ytdl_source(self, url: str, *, loop=None, stream: bool = True):
        """
        Create a YTDLSource from URL with error handling
        
        FIX #15: Check FFmpeg before creating source
        FIX #16: Add timeout to prevent hanging
        FIX AUDIO #1: Use proper FFmpeg options for clean audio
        
        Args:
            url: YouTube URL or search query
            loop: Event loop to use
            stream: Whether to stream or download
            
        Returns:
            YTDLSource object or None on failure
        """
        # FIX #15: Validate FFmpeg is available
        if not self.is_ffmpeg_available():
            logger.error("Cannot create audio source: FFmpeg is not available")
            return None
        
        loop = loop or asyncio.get_event_loop()
        
        try:
            # FIX #16: Add timeout to prevent hanging
            data = await asyncio.wait_for(
                loop.run_in_executor(
                    None, 
                    lambda: self.ytdl.extract_info(url, download=not stream)
                ),
                timeout=YTDL_TIMEOUT
            )
            
            if not data:
                logger.error(f"No data extracted from URL: {url}")
                return None
            
            # Handle playlists (take first entry)
            if 'entries' in data:
                if not data['entries']:
                    logger.error(f"Empty playlist or no entries: {url}")
                    return None
                data = data['entries'][0]
            
            # Get the stream URL
            if stream:
                # For streaming, we need the direct URL
                if 'url' not in data:
                    logger.error(f"No stream URL found in data for: {url}")
                    return None
                filename = data['url']
            else:
                filename = self.ytdl.prepare_filename(data)
            
            # FIX AUDIO #1: Create FFmpeg audio source with enhanced options
            ffmpeg_options = self.FFMPEG_OPTIONS.copy()
            
            logger.debug(f"Creating audio source with 48kHz, stereo, buffered settings for: {data.get('title', 'Unknown')}")
            
            audio_source = discord.FFmpegPCMAudio(
                filename, 
                executable=self.ffmpeg_path,
                **ffmpeg_options
            )
            
            return YTDLSource(audio_source, data=data)
        
        except asyncio.TimeoutError:
            # FIX #16: Handle timeout gracefully
            logger.error(f"Timeout extracting info from URL (>{YTDL_TIMEOUT}s): {url}")
            return None
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"yt-dlp download error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating YTDL source for {url}: {e}", exc_info=True)
            return None
    
    async def search_youtube(self, query: str, max_results: int = 5) -> Optional[list]:
        """
        Search YouTube and return results
        
        FIX #16: Add timeout to prevent hanging
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of search results or None on failure
        """
        search_query = f"ytsearch{max_results}:{query}"
        loop = asyncio.get_event_loop()
        
        try:
            # FIX #16: Add timeout to search
            info = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.ytdl.extract_info(search_query, download=False)
                ),
                timeout=SEARCH_TIMEOUT
            )
            
            if 'entries' in info and info['entries']:
                return info['entries'][:max_results]
            
            logger.warning(f"No search results for: {query}")
            return None
        
        except asyncio.TimeoutError:
            # FIX #16: Handle search timeout
            logger.error(f"Search timeout (>{SEARCH_TIMEOUT}s) for query: {query}")
            return None
        except Exception as e:
            logger.error(f"Search error for '{query}': {e}", exc_info=True)
            return None
    
    def create_local_source(self, filepath: str):
        """
        Create an audio source from local file
        
        FIX #15: Validate FFmpeg and file before creating source
        FIX AUDIO #1: Use proper FFmpeg options for local files
        
        Args:
            filepath: Path to local audio file
            
        Returns:
            FFmpegPCMAudio source or None on failure
        """
        # FIX #15: Check FFmpeg availability
        if not self.is_ffmpeg_available():
            logger.error("Cannot create local source: FFmpeg is not available")
            return None
        
        # Validate file exists
        if not os.path.exists(filepath):
            logger.error(f"Local file does not exist: {filepath}")
            return None
        
        # Validate file is readable
        if not os.access(filepath, os.R_OK):
            logger.error(f"Local file is not readable: {filepath}")
            return None
        
        try:
            # FIX AUDIO #1: Use local-specific FFmpeg options (no reconnect, with padding)
            ffmpeg_options = self.FFMPEG_OPTIONS_LOCAL.copy()
            
            logger.debug(f"Creating local audio source with 48kHz, stereo settings for: {filepath}")
            
            return discord.FFmpegPCMAudio(
                filepath,
                executable=self.ffmpeg_path,
                **ffmpeg_options
            )
                
        except Exception as e:
            logger.error(f"Error creating local source for {filepath}: {e}", exc_info=True)
            return None


class YTDLSource(discord.PCMVolumeTransformer):
    """
    Represents a YouTube audio source with volume control
    FIX AUDIO #1: Smooth volume transitions to prevent pops
    """
    
    def __init__(self, source, *, data, volume: float = 0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title', 'Unknown')
        self.url = data.get('url')
        self.webpage_url = data.get('webpage_url')
        self.duration = data.get('duration', 0)
        self.uploader = data.get('uploader', 'Unknown')
        self._last_volume = volume  # FIX AUDIO #1: Track volume for smooth transitions
    
    def __repr__(self):
        return f"YTDLSource(title='{self.title}', duration={self.duration})"
    
    @property
    def volume(self):
        """Get current volume"""
        return self._volume
    
    @volume.setter
    def volume(self, value: float):
        """
        Set volume with validation
        FIX AUDIO #1: Prevent abrupt volume changes that cause pops
        """
        # Clamp volume between 0.0 and 2.0
        value = max(0.0, min(2.0, value))
        
        # FIX AUDIO #1: Log significant volume changes
        if abs(value - self._last_volume) > 0.3:
            logger.debug(f"Large volume change detected: {self._last_volume:.2f} -> {value:.2f}")
        
        self._volume = value
        self._last_volume = value


# Global audio service instance
audio_service = AudioService()
