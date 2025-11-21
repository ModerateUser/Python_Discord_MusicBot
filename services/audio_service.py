"""
Audio streaming and playback service
Handles YouTube downloads and audio source creation
"""
import discord
import yt_dlp
import asyncio
from typing import Optional

class AudioService:
    """Handles audio streaming and source creation"""
    
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
    }
    
    FFMPEG_OPTIONS = {
        'options': '-vn'
    }
    
    def __init__(self):
        self.ytdl = yt_dlp.YoutubeDL(self.YTDL_OPTIONS)
    
    async def create_ytdl_source(self, url: str, *, loop=None, stream: bool = True):
        """Create a YTDLSource from URL"""
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, 
            lambda: self.ytdl.extract_info(url, download=not stream)
        )
        
        if 'entries' in data:
            data = data['entries'][0]
        
        filename = data['url'] if stream else self.ytdl.prepare_filename(data)
        return YTDLSource(discord.FFmpegPCMAudio(filename, **self.FFMPEG_OPTIONS), data=data)
    
    async def search_youtube(self, query: str, max_results: int = 5) -> Optional[list]:
        """Search YouTube and return results"""
        search_query = f"ytsearch{max_results}:{query}"
        loop = asyncio.get_event_loop()
        
        try:
            info = await loop.run_in_executor(
                None,
                lambda: self.ytdl.extract_info(search_query, download=False)
            )
            
            if 'entries' in info:
                return info['entries'][:max_results]
            return None
        except Exception as e:
            print(f"Search error: {e}")
            return None
    
    def create_local_source(self, filepath: str):
        """Create an audio source from local file"""
        return discord.FFmpegPCMAudio(filepath)

class YTDLSource(discord.PCMVolumeTransformer):
    """Represents a YouTube audio source"""
    
    def __init__(self, source, *, data, volume: float = 0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')

# Global audio service instance
audio_service = AudioService()
