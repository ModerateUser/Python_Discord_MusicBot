"""
Audio streaming and playback service
Handles YouTube downloads and audio source creation
"""
import discord
import yt_dlp
import asyncio
import logging
import shutil
from typing import Optional

logger = logging.getLogger('discord_bot')

class AudioService:
    """Handles audio streaming and source creation"""
    
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
    }
    
    # FFmpeg options with reconnect support for streaming
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -loglevel warning'
    }
    
    def __init__(self):
        self.ytdl = yt_dlp.YoutubeDL(self.YTDL_OPTIONS)
        self.ffmpeg_path = self._find_ffmpeg()
        
        if not self.ffmpeg_path:
            logger.warning("FFmpeg not found in PATH. Audio playback may fail.")
        else:
            logger.info(f"FFmpeg found at: {self.ffmpeg_path}")
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Find FFmpeg executable in system PATH"""
        ffmpeg = shutil.which('ffmpeg')
        if ffmpeg:
            return ffmpeg
        
        # Try common Windows locations
        import os
        common_paths = [
            r'C:\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe',
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    async def create_ytdl_source(self, url: str, *, loop=None, stream: bool = True):
        """
        Create a YTDLSource from URL with error handling
        
        Args:
            url: YouTube URL or search query
            loop: Event loop to use
            stream: Whether to stream or download
            
        Returns:
            YTDLSource object or None on failure
        """
        loop = loop or asyncio.get_event_loop()
        
        try:
            data = await loop.run_in_executor(
                None, 
                lambda: self.ytdl.extract_info(url, download=not stream)
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
            
            # Create FFmpeg audio source with proper options
            ffmpeg_options = self.FFMPEG_OPTIONS.copy()
            if self.ffmpeg_path:
                audio_source = discord.FFmpegPCMAudio(
                    filename, 
                    executable=self.ffmpeg_path,
                    **ffmpeg_options
                )
            else:
                audio_source = discord.FFmpegPCMAudio(filename, **ffmpeg_options)
            
            return YTDLSource(audio_source, data=data)
            
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"yt-dlp download error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating YTDL source for {url}: {e}", exc_info=True)
            return None
    
    async def search_youtube(self, query: str, max_results: int = 5) -> Optional[list]:
        """
        Search YouTube and return results
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of search results or None on failure
        """
        search_query = f"ytsearch{max_results}:{query}"
        loop = asyncio.get_event_loop()
        
        try:
            info = await loop.run_in_executor(
                None,
                lambda: self.ytdl.extract_info(search_query, download=False)
            )
            
            if 'entries' in info and info['entries']:
                return info['entries'][:max_results]
            
            logger.warning(f"No search results for: {query}")
            return None
            
        except Exception as e:
            logger.error(f"Search error for '{query}': {e}", exc_info=True)
            return None
    
    def create_local_source(self, filepath: str):
        """
        Create an audio source from local file
        
        Args:
            filepath: Path to local audio file
            
        Returns:
            FFmpegPCMAudio source
        """
        try:
            ffmpeg_options = self.FFMPEG_OPTIONS.copy()
            # Remove reconnect options for local files
            ffmpeg_options['before_options'] = ''
            
            if self.ffmpeg_path:
                return discord.FFmpegPCMAudio(
                    filepath,
                    executable=self.ffmpeg_path,
                    **ffmpeg_options
                )
            else:
                return discord.FFmpegPCMAudio(filepath, **ffmpeg_options)
                
        except Exception as e:
            logger.error(f"Error creating local source for {filepath}: {e}", exc_info=True)
            return None

class YTDLSource(discord.PCMVolumeTransformer):
    """Represents a YouTube audio source with volume control"""
    
    def __init__(self, source, *, data, volume: float = 0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title', 'Unknown')
        self.url = data.get('url')
        self.webpage_url = data.get('webpage_url')
        self.duration = data.get('duration', 0)
        self.uploader = data.get('uploader', 'Unknown')
        
    def __repr__(self):
        return f"YTDLSource(title='{self.title}', duration={self.duration})"

# Global audio service instance
audio_service = AudioService()
