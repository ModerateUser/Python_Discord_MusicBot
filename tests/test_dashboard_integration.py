"""
Comprehensive Dashboard Integration Test Suite
Tests the complete integration between bot, dashboard bridge, and web dashboard
"""
import asyncio
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import discord
from discord.ext import commands

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.dashboard_bridge import DashboardBridge, BotStatus, QueueInfo
from models.song import Song, MusicQueue


class MockBot:
    """Mock Discord bot for testing"""
    
    def __init__(self):
        self.user = Mock()
        self.user.id = 123456789
        self.user.name = "TestBot"
        self.guilds = []
        self.latency = 0.05
        self.loop = asyncio.get_event_loop()
        self._cogs = {}
        self._ready = True
        self._closed = False
    
    def is_ready(self):
        return self._ready
    
    def is_closed(self):
        return self._closed
    
    def get_guild(self, guild_id):
        for guild in self.guilds:
            if guild.id == guild_id:
                return guild
        return None
    
    def get_cog(self, name):
        return self._cogs.get(name)
    
    def add_cog(self, name, cog):
        self._cogs[name] = cog


class MockGuild:
    """Mock Discord guild"""
    
    def __init__(self, guild_id, name, member_count=100):
        self.id = guild_id
        self.name = name
        self.member_count = member_count
        self.icon = None
        self.voice_client = None


class MockVoiceClient:
    """Mock Discord voice client"""
    
    def __init__(self, channel):
        self.channel = channel
        self.source = None
        self._playing = False
        self._paused = False
    
    def is_playing(self):
        return self._playing
    
    def is_paused(self):
        return self._paused
    
    def play(self, source, after=None):
        self.source = source
        self._playing = True
        self._paused = False
    
    def pause(self):
        if self._playing:
            self._paused = True
    
    def resume(self):
        if self._paused:
            self._paused = False
    
    def stop(self):
        self._playing = False
        self._paused = False
        if after := getattr(self, '_after', None):
            after(None)


class MockMusicCog:
    """Mock Music cog"""
    
    def __init__(self):
        self.queues = {}
    
    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = MusicQueue()
        return self.queues[guild_id]


class MockWebSocketManager:
    """Mock WebSocket manager"""
    
    def __init__(self):
        self.messages = []
    
    async def broadcast(self, message):
        self.messages.append(message)


@pytest.fixture
def mock_bot():
    """Create mock bot"""
    return MockBot()


@pytest.fixture
def mock_guild():
    """Create mock guild"""
    guild = MockGuild(987654321, "Test Guild", 150)
    channel = Mock()
    channel.name = "Music"
    guild.voice_client = MockVoiceClient(channel)
    return guild


@pytest.fixture
def mock_music_cog():
    """Create mock music cog"""
    return MockMusicCog()


@pytest.fixture
async def dashboard_bridge(mock_bot, mock_music_cog):
    """Create dashboard bridge with mocked dependencies"""
    mock_bot.add_cog('Music', mock_music_cog)
    bridge = DashboardBridge(mock_bot)
    yield bridge
    await bridge.stop()


@pytest.mark.asyncio
async def test_dashboard_bridge_initialization(mock_bot):
    """Test dashboard bridge initializes correctly"""
    bridge = DashboardBridge(mock_bot)
    
    assert bridge.bot == mock_bot
    assert bridge.start_time is not None
    assert len(bridge._subscribers) == 0
    assert bridge.websocket_manager is None
    
    await bridge.stop()


@pytest.mark.asyncio
async def test_get_bot_status(dashboard_bridge, mock_bot, mock_guild):
    """Test getting bot status"""
    mock_bot.guilds = [mock_guild]
    
    status = await dashboard_bridge.get_bot_status()
    
    assert isinstance(status, BotStatus)
    assert status.connected == True
    assert status.status == "online"
    assert len(status.guilds) == 1
    assert status.guilds[0]['id'] == mock_guild.id
    assert status.guilds[0]['name'] == mock_guild.name
    assert status.total_users == 150


@pytest.mark.asyncio
async def test_get_guild_queue_with_songs(dashboard_bridge, mock_bot, mock_guild, mock_music_cog):
    """Test getting guild queue with songs"""
    mock_bot.guilds = [mock_guild]
    
    # Add songs to queue
    queue = mock_music_cog.get_queue(mock_guild.id)
    song1 = Song("test.mp3", "Test Song 1", is_local=True)
    song2 = Song("test2.mp3", "Test Song 2", is_local=True)
    queue.add(song1)
    queue.add(song2)
    queue.current = song1
    
    # Set voice client to playing
    mock_guild.voice_client._playing = True
    
    queue_info = await dashboard_bridge.get_guild_queue(mock_guild.id)
    
    assert isinstance(queue_info, QueueInfo)
    assert queue_info.guild_id == mock_guild.id
    assert queue_info.guild_name == mock_guild.name
    assert queue_info.current_song is not None
    assert queue_info.current_song['title'] == "Test Song 1"
    assert queue_info.is_playing == True
    assert queue_info.is_paused == False
    assert queue_info.queue_length == 2


@pytest.mark.asyncio
async def test_get_guild_queue_empty(dashboard_bridge, mock_bot, mock_guild):
    """Test getting empty guild queue"""
    mock_bot.guilds = [mock_guild]
    
    queue_info = await dashboard_bridge.get_guild_queue(mock_guild.id)
    
    assert isinstance(queue_info, QueueInfo)
    assert queue_info.current_song is None
    assert len(queue_info.queue) == 0
    assert queue_info.queue_length == 0


@pytest.mark.asyncio
async def test_execute_command_pause(dashboard_bridge, mock_bot, mock_guild):
    """Test pause command execution"""
    mock_bot.guilds = [mock_guild]
    mock_guild.voice_client._playing = True
    
    result = await dashboard_bridge.execute_command(mock_guild.id, 'pause')
    
    assert result['success'] == True
    assert result['message'] == "Paused"
    assert mock_guild.voice_client.is_paused() == True


@pytest.mark.asyncio
async def test_execute_command_resume(dashboard_bridge, mock_bot, mock_guild):
    """Test resume command execution"""
    mock_bot.guilds = [mock_guild]
    mock_guild.voice_client._playing = True
    mock_guild.voice_client._paused = True
    
    result = await dashboard_bridge.execute_command(mock_guild.id, 'resume')
    
    assert result['success'] == True
    assert result['message'] == "Resumed"
    assert mock_guild.voice_client.is_paused() == False


@pytest.mark.asyncio
async def test_execute_command_skip(dashboard_bridge, mock_bot, mock_guild):
    """Test skip command execution"""
    mock_bot.guilds = [mock_guild]
    mock_guild.voice_client._playing = True
    
    result = await dashboard_bridge.execute_command(mock_guild.id, 'skip')
    
    assert result['success'] == True
    assert result['message'] == "Skipped"


@pytest.mark.asyncio
async def test_execute_command_volume(dashboard_bridge, mock_bot, mock_guild, mock_music_cog):
    """Test volume command execution"""
    mock_bot.guilds = [mock_guild]
    queue = mock_music_cog.get_queue(mock_guild.id)
    
    result = await dashboard_bridge.execute_command(mock_guild.id, 'volume', volume=75)
    
    assert result['success'] == True
    assert "75%" in result['message']
    assert queue.volume == 0.75


@pytest.mark.asyncio
async def test_execute_command_volume_invalid(dashboard_bridge, mock_bot, mock_guild):
    """Test volume command with invalid value"""
    mock_bot.guilds = [mock_guild]
    
    result = await dashboard_bridge.execute_command(mock_guild.id, 'volume', volume=150)
    
    assert result['success'] == False
    assert "must be 0-100" in result['error']


@pytest.mark.asyncio
async def test_execute_command_loop(dashboard_bridge, mock_bot, mock_guild, mock_music_cog):
    """Test loop command execution"""
    mock_bot.guilds = [mock_guild]
    queue = mock_music_cog.get_queue(mock_guild.id)
    
    # Enable loop
    result = await dashboard_bridge.execute_command(mock_guild.id, 'loop')
    assert result['success'] == True
    assert "enabled" in result['message']
    assert queue.loop == True
    
    # Disable loop
    result = await dashboard_bridge.execute_command(mock_guild.id, 'loop')
    assert result['success'] == True
    assert "disabled" in result['message']
    assert queue.loop == False


@pytest.mark.asyncio
async def test_execute_command_stop(dashboard_bridge, mock_bot, mock_guild, mock_music_cog):
    """Test stop command execution"""
    mock_bot.guilds = [mock_guild]
    queue = mock_music_cog.get_queue(mock_guild.id)
    
    # Add songs
    queue.add(Song("test.mp3", "Test Song", is_local=True))
    mock_guild.voice_client._playing = True
    
    result = await dashboard_bridge.execute_command(mock_guild.id, 'stop')
    
    assert result['success'] == True
    assert result['message'] == "Stopped"
    assert len(queue.songs) == 0


@pytest.mark.asyncio
async def test_execute_command_unknown(dashboard_bridge, mock_bot, mock_guild):
    """Test unknown command execution"""
    mock_bot.guilds = [mock_guild]
    
    result = await dashboard_bridge.execute_command(mock_guild.id, 'unknown_command')
    
    assert result['success'] == False
    assert "Unknown command" in result['error']


@pytest.mark.asyncio
async def test_execute_command_no_voice_client(dashboard_bridge, mock_bot, mock_guild):
    """Test command execution without voice client"""
    mock_bot.guilds = [mock_guild]
    mock_guild.voice_client = None
    
    result = await dashboard_bridge.execute_command(mock_guild.id, 'pause')
    
    assert result['success'] == False
    assert "not in voice channel" in result['error']


@pytest.mark.asyncio
async def test_websocket_broadcast(dashboard_bridge, mock_bot):
    """Test WebSocket broadcasting"""
    ws_manager = MockWebSocketManager()
    dashboard_bridge.set_websocket_manager(ws_manager)
    
    await dashboard_bridge._broadcast_update('test_event', {'data': 'test'})
    
    assert len(ws_manager.messages) == 1
    assert ws_manager.messages[0]['type'] == 'test_event'
    assert ws_manager.messages[0]['data']['data'] == 'test'


@pytest.mark.asyncio
async def test_subscriber_notification(dashboard_bridge):
    """Test subscriber notification system"""
    received_messages = []
    
    async def subscriber(message):
        received_messages.append(message)
    
    dashboard_bridge.subscribe(subscriber)
    
    await dashboard_bridge._broadcast_update('test_event', {'key': 'value'})
    
    # Give async tasks time to complete
    await asyncio.sleep(0.1)
    
    assert len(received_messages) == 1
    assert received_messages[0]['type'] == 'test_event'


@pytest.mark.asyncio
async def test_on_track_start_notification(dashboard_bridge):
    """Test track start notification"""
    ws_manager = MockWebSocketManager()
    dashboard_bridge.set_websocket_manager(ws_manager)
    
    track_info = {'title': 'Test Song', 'is_local': True}
    dashboard_bridge.on_track_start(123, track_info)
    
    # Give async task time to complete
    await asyncio.sleep(0.1)
    
    assert len(ws_manager.messages) == 1
    assert ws_manager.messages[0]['type'] == 'track_start'
    assert ws_manager.messages[0]['data']['guild_id'] == 123


@pytest.mark.asyncio
async def test_on_track_end_notification(dashboard_bridge):
    """Test track end notification"""
    ws_manager = MockWebSocketManager()
    dashboard_bridge.set_websocket_manager(ws_manager)
    
    dashboard_bridge.on_track_end(123)
    
    # Give async task time to complete
    await asyncio.sleep(0.1)
    
    assert len(ws_manager.messages) == 1
    assert ws_manager.messages[0]['type'] == 'track_end'
    assert ws_manager.messages[0]['data']['guild_id'] == 123


@pytest.mark.asyncio
async def test_on_queue_update_notification(dashboard_bridge):
    """Test queue update notification"""
    ws_manager = MockWebSocketManager()
    dashboard_bridge.set_websocket_manager(ws_manager)
    
    dashboard_bridge.on_queue_update(123)
    
    # Give async task time to complete
    await asyncio.sleep(0.1)
    
    assert len(ws_manager.messages) == 1
    assert ws_manager.messages[0]['type'] == 'queue_update'
    assert ws_manager.messages[0]['data']['guild_id'] == 123


@pytest.mark.asyncio
async def test_get_all_queues(dashboard_bridge, mock_bot, mock_music_cog):
    """Test getting all queues"""
    # Create multiple guilds with queues
    guild1 = MockGuild(111, "Guild 1")
    guild2 = MockGuild(222, "Guild 2")
    
    channel = Mock()
    channel.name = "Music"
    guild1.voice_client = MockVoiceClient(channel)
    guild2.voice_client = MockVoiceClient(channel)
    
    mock_bot.guilds = [guild1, guild2]
    
    # Add songs to queues
    queue1 = mock_music_cog.get_queue(111)
    queue1.add(Song("test1.mp3", "Song 1", is_local=True))
    
    queue2 = mock_music_cog.get_queue(222)
    queue2.add(Song("test2.mp3", "Song 2", is_local=True))
    
    queues = await dashboard_bridge.get_all_queues()
    
    assert len(queues) == 2
    assert all(isinstance(q, QueueInfo) for q in queues)


@pytest.mark.asyncio
async def test_service_health(dashboard_bridge, mock_bot):
    """Test service health check"""
    mock_bot._ready = True
    
    health = await dashboard_bridge.get_service_health()
    
    assert health['bot'] == True
    assert health['dashboard_bridge'] == True


@pytest.mark.asyncio
async def test_periodic_update_task(dashboard_bridge, mock_bot):
    """Test periodic update task"""
    ws_manager = MockWebSocketManager()
    dashboard_bridge.set_websocket_manager(ws_manager)
    
    await dashboard_bridge.start()
    
    # Wait for at least one update cycle
    await asyncio.sleep(6)
    
    # Should have received status updates
    assert len(ws_manager.messages) > 0
    
    await dashboard_bridge.stop()


@pytest.mark.asyncio
async def test_bot_status_to_dict(dashboard_bridge, mock_bot, mock_guild):
    """Test BotStatus serialization"""
    mock_bot.guilds = [mock_guild]
    
    status = await dashboard_bridge.get_bot_status()
    status_dict = status.to_dict()
    
    assert isinstance(status_dict, dict)
    assert 'connected' in status_dict
    assert 'status' in status_dict
    assert 'guilds' in status_dict
    assert 'uptime' in status_dict
    assert 'start_time' in status_dict


@pytest.mark.asyncio
async def test_queue_info_to_dict(dashboard_bridge, mock_bot, mock_guild, mock_music_cog):
    """Test QueueInfo serialization"""
    mock_bot.guilds = [mock_guild]
    
    queue = mock_music_cog.get_queue(mock_guild.id)
    queue.add(Song("test.mp3", "Test Song", is_local=True))
    
    queue_info = await dashboard_bridge.get_guild_queue(mock_guild.id)
    queue_dict = queue_info.to_dict()
    
    assert isinstance(queue_dict, dict)
    assert 'guild_id' in queue_dict
    assert 'guild_name' in queue_dict
    assert 'current_song' in queue_dict
    assert 'queue' in queue_dict
    assert 'is_playing' in queue_dict


def test_global_bridge_instance():
    """Test global bridge instance management"""
    from services.dashboard_bridge import get_dashboard_bridge, set_dashboard_bridge
    
    mock_bot = MockBot()
    bridge = DashboardBridge(mock_bot)
    
    set_dashboard_bridge(bridge)
    retrieved = get_dashboard_bridge()
    
    assert retrieved == bridge


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--asyncio-mode=auto'])
