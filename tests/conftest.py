"""
Pytest configuration and fixtures for Discord Music Bot tests
"""
import pytest
import asyncio
import discord
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any
import tempfile
import os

# Import bot components
from models.song import Song, MusicQueue
from services.audio_service import AudioService
from core.config import Config


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_bot():
    """Create a mock Discord bot"""
    bot = Mock(spec=discord.ext.commands.Bot)
    bot.user = Mock(spec=discord.User)
    bot.user.name = "TestBot"
    bot.user.id = 123456789
    bot.loop = asyncio.get_event_loop()
    bot.guilds = []
    return bot


@pytest.fixture
def mock_guild():
    """Create a mock Discord guild"""
    guild = Mock(spec=discord.Guild)
    guild.id = 987654321
    guild.name = "Test Guild"
    guild.voice_client = None
    return guild


@pytest.fixture
def mock_voice_channel():
    """Create a mock voice channel"""
    channel = Mock(spec=discord.VoiceChannel)
    channel.id = 111222333
    channel.name = "Test Voice"
    channel.guild = Mock(spec=discord.Guild)
    channel.guild.id = 987654321
    return channel


@pytest.fixture
def mock_text_channel():
    """Create a mock text channel"""
    channel = Mock(spec=discord.TextChannel)
    channel.id = 444555666
    channel.name = "test-channel"
    channel.send = AsyncMock()
    return channel


@pytest.fixture
def mock_author():
    """Create a mock message author"""
    author = Mock(spec=discord.Member)
    author.id = 777888999
    author.name = "TestUser"
    author.voice = Mock()
    author.voice.channel = Mock(spec=discord.VoiceChannel)
    author.voice.channel.id = 111222333
    return author


@pytest.fixture
def mock_context(mock_bot, mock_guild, mock_text_channel, mock_author):
    """Create a mock command context"""
    ctx = Mock(spec=discord.ext.commands.Context)
    ctx.bot = mock_bot
    ctx.guild = mock_guild
    ctx.channel = mock_text_channel
    ctx.author = mock_author
    ctx.voice_client = None
    ctx.send = AsyncMock()
    ctx.typing = AsyncMock()
    ctx.typing.return_value.__aenter__ = AsyncMock()
    ctx.typing.return_value.__aexit__ = AsyncMock()
    return ctx


@pytest.fixture
def mock_voice_client():
    """Create a mock voice client"""
    vc = Mock(spec=discord.VoiceClient)
    vc.is_connected = Mock(return_value=True)
    vc.is_playing = Mock(return_value=False)
    vc.is_paused = Mock(return_value=False)
    vc.play = Mock()
    vc.pause = Mock()
    vc.resume = Mock()
    vc.stop = Mock()
    vc.disconnect = AsyncMock()
    vc.move_to = AsyncMock()
    return vc


@pytest.fixture
def sample_song():
    """Create a sample song object"""
    return Song(
        source="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title="Test Song",
        is_local=False
    )


@pytest.fixture
def sample_local_song(tmp_path):
    """Create a sample local song with temp file"""
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_text("fake audio data")
    return Song(
        source=str(audio_file),
        title="Local Test Song",
        is_local=True
    )


@pytest.fixture
def music_queue():
    """Create a fresh music queue"""
    return MusicQueue()


@pytest.fixture
def populated_queue(sample_song):
    """Create a queue with sample songs"""
    queue = MusicQueue()
    for i in range(3):
        song = Song(
            source=f"https://example.com/song{i}",
            title=f"Test Song {i}",
            is_local=False
        )
        queue.add(song)
    return queue


@pytest.fixture
def mock_ytdl_data():
    """Mock yt-dlp extraction data"""
    return {
        'title': 'Test Video',
        'url': 'https://example.com/stream.m3u8',
        'webpage_url': 'https://www.youtube.com/watch?v=test123',
        'duration': 180,
        'uploader': 'Test Channel',
        'id': 'test123',
        'ext': 'webm'
    }


@pytest.fixture
def mock_audio_service(monkeypatch):
    """Create a mock audio service"""
    service = Mock(spec=AudioService)
    service.is_ffmpeg_available = Mock(return_value=True)
    service.create_ytdl_source = AsyncMock()
    service.search_youtube = AsyncMock()
    service.create_local_source = Mock()
    return service


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file"""
    config_file = tmp_path / "config.json"
    config_data = {
        "discord_token": "test_token_123",
        "command_prefix": "!",
        "max_queue_size": 100,
        "allowed_file_extensions": [".mp3", ".wav", ".ogg"],
        "music_directory": str(tmp_path / "music"),
        "enable_ai_features": False
    }
    
    import json
    config_file.write_text(json.dumps(config_data, indent=2))
    return config_file


@pytest.fixture
def mock_config(temp_config_file):
    """Create a mock config object"""
    config = Config(str(temp_config_file))
    return config


@pytest.fixture
def mock_llm_response():
    """Mock LLM response data"""
    return {
        "actions": [
            {
                "action": "play",
                "query": "test song",
                "reason": "User requested to play a song"
            }
        ]
    }


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service"""
    service = Mock()
    service.generate_response = AsyncMock()
    service.is_available = Mock(return_value=True)
    return service


@pytest.fixture
async def cleanup_tasks():
    """Cleanup any pending asyncio tasks after test"""
    yield
    # Cancel any pending tasks
    tasks = [t for t in asyncio.all_tasks() if not t.done()]
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


@pytest.fixture
def mock_ffmpeg_audio():
    """Create a mock FFmpeg audio source"""
    audio = Mock(spec=discord.FFmpegPCMAudio)
    audio.cleanup = Mock()
    audio.read = Mock(return_value=b'\x00' * 3840)  # Mock audio data
    return audio


@pytest.fixture
def mock_ytdl_source(mock_ytdl_data):
    """Create a mock YTDLSource"""
    from services.audio_service import YTDLSource
    
    mock_source = Mock(spec=discord.FFmpegPCMAudio)
    ytdl_source = Mock(spec=YTDLSource)
    ytdl_source.data = mock_ytdl_data
    ytdl_source.title = mock_ytdl_data['title']
    ytdl_source.url = mock_ytdl_data['url']
    ytdl_source.webpage_url = mock_ytdl_data['webpage_url']
    ytdl_source.duration = mock_ytdl_data['duration']
    ytdl_source.volume = 0.5
    ytdl_source.cleanup = Mock()
    
    return ytdl_source


# Pytest markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_ffmpeg: mark test as requiring FFmpeg"
    )
    config.addinivalue_line(
        "markers", "requires_llm: mark test as requiring LLM service"
    )


# Helper functions for tests
def create_mock_cog(bot, cog_class):
    """Helper to create a mock cog instance"""
    cog = cog_class(bot)
    return cog


async def wait_for_voice_client(ctx, timeout=1.0):
    """Helper to wait for voice client connection"""
    start = asyncio.get_event_loop().time()
    while not ctx.voice_client:
        if asyncio.get_event_loop().time() - start > timeout:
            raise TimeoutError("Voice client connection timeout")
        await asyncio.sleep(0.1)
    return ctx.voice_client
