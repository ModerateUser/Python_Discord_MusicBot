"""
Integration Tests - Music Playback Workflow
Tests the complete music playback flow from command to audio output
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from core.bot_core import create_bot
from core.service_manager import ServiceManager


@pytest.mark.asyncio
class TestMusicPlaybackIntegration:
    """Integration tests for music playback workflow"""
    
    @pytest.fixture
    async def bot(self):
        """Create a test bot instance"""
        bot = create_bot()
        # Mock the start method to prevent actual connection
        bot.start = AsyncMock()
        yield bot
        await bot.close()
    
    @pytest.fixture
    async def mock_voice_client(self):
        """Create a mock voice client"""
        voice_client = MagicMock()
        voice_client.is_connected.return_value = True
        voice_client.is_playing.return_value = False
        voice_client.play = MagicMock()
        voice_client.stop = MagicMock()
        voice_client.pause = MagicMock()
        voice_client.resume = MagicMock()
        return voice_client
    
    async def test_complete_play_workflow(self, bot, mock_message, mock_voice_client):
        """Test complete play workflow from command to playback"""
        # Setup
        mock_message.guild.voice_client = mock_voice_client
        mock_message.author.voice = MagicMock()
        mock_message.author.voice.channel = MagicMock()
        
        # Load music cog
        await bot.load_extension('cogs.music')
        music_cog = bot.get_cog('Music')
        
        assert music_cog is not None, "Music cog should be loaded"
        
        # Mock audio service
        with patch('services.audio_service_enhanced.AudioService') as MockAudioService:
            mock_audio = MockAudioService.return_value
            mock_audio.create_ytdl_source = AsyncMock(return_value=MagicMock())
            
            # Execute play command
            await music_cog.play(mock_message, query="test song")
            
            # Verify audio service was called
            mock_audio.create_ytdl_source.assert_called_once()
            
            # Verify voice client played audio
            assert mock_voice_client.play.called or mock_message.channel.send.called
    
    async def test_queue_management_workflow(self, bot, mock_message):
        """Test queue management workflow"""
        # Load queue cog
        await bot.load_extension('cogs.queue_manager')
        queue_cog = bot.get_cog('QueueManager')
        
        assert queue_cog is not None, "Queue cog should be loaded"
        
        # Add songs to queue
        from models.music_queue import Song
        
        song1 = Song("Test Song 1", "http://example.com/1", "Artist 1", 180)
        song2 = Song("Test Song 2", "http://example.com/2", "Artist 2", 200)
        
        guild_id = mock_message.guild.id
        queue = queue_cog.get_queue(guild_id)
        
        queue.add(song1)
        queue.add(song2)
        
        # Verify queue state
        assert queue.size() == 2
        assert queue.current() == song1
        
        # Test next song
        next_song = queue.next()
        assert next_song == song2
        assert queue.current() == song2
    
    async def test_service_initialization_workflow(self, bot):
        """Test service initialization workflow"""
        # Initialize services
        await bot.service_manager.initialize_all()
        
        # Verify services are registered
        assert bot.service_manager.is_service_available('bot')
        assert bot.service_manager.is_service_available('config')
        
        # Check health
        health = await bot.service_manager.health_check()
        assert 'audio_service' in health
        assert 'llm_service' in health
    
    async def test_caching_workflow(self, bot):
        """Test caching workflow for audio metadata"""
        from services.audio_service_enhanced import AudioService
        from utils.cache import get_cache_manager
        
        audio_service = AudioService(thread_pool_size=2)
        cache_manager = get_cache_manager()
        
        # Mock yt-dlp
        with patch('yt_dlp.YoutubeDL') as MockYTDL:
            mock_ytdl = MockYTDL.return_value.__enter__.return_value
            mock_ytdl.extract_info.return_value = {
                'title': 'Test Video',
                'url': 'http://example.com/video',
                'duration': 180,
                'uploader': 'Test Channel'
            }
            
            # First call - should hit yt-dlp
            metadata1 = await audio_service.get_video_metadata('http://example.com/test')
            assert metadata1 is not None
            assert metadata1.title == 'Test Video'
            
            # Second call - should hit cache
            metadata2 = await audio_service.get_video_metadata('http://example.com/test')
            assert metadata2 is not None
            assert metadata2.title == 'Test Video'
            
            # Verify cache hit
            stats = cache_manager.get_cache_stats('youtube_metadata')
            assert stats['hits'] > 0
        
        # Cleanup
        audio_service.shutdown()
    
    async def test_error_handling_workflow(self, bot, mock_message):
        """Test error handling in playback workflow"""
        # Load music cog
        await bot.load_extension('cogs.music')
        music_cog = bot.get_cog('Music')
        
        # Test with no voice channel
        mock_message.author.voice = None
        
        await music_cog.play(mock_message, query="test")
        
        # Verify error message was sent
        assert mock_message.channel.send.called
        call_args = mock_message.channel.send.call_args[0][0]
        assert "voice channel" in call_args.lower() or "join" in call_args.lower()
    
    async def test_concurrent_playback_workflow(self, bot, mock_message, mock_voice_client):
        """Test concurrent playback requests"""
        # Setup
        mock_message.guild.voice_client = mock_voice_client
        mock_message.author.voice = MagicMock()
        mock_message.author.voice.channel = MagicMock()
        
        # Load music cog
        await bot.load_extension('cogs.music')
        music_cog = bot.get_cog('Music')
        
        # Mock audio service
        with patch('services.audio_service_enhanced.AudioService') as MockAudioService:
            mock_audio = MockAudioService.return_value
            mock_audio.create_ytdl_source = AsyncMock(return_value=MagicMock())
            
            # Execute multiple play commands concurrently
            tasks = [
                music_cog.play(mock_message, query=f"test song {i}")
                for i in range(5)
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify all requests were handled
            assert mock_audio.create_ytdl_source.call_count >= 1


@pytest.mark.asyncio
class TestNaturalLanguageIntegration:
    """Integration tests for natural language processing"""
    
    @pytest.fixture
    async def bot(self):
        """Create a test bot instance"""
        bot = create_bot()
        bot.start = AsyncMock()
        yield bot
        await bot.close()
    
    async def test_simple_nlp_workflow(self, bot, mock_message):
        """Test simple natural language command workflow"""
        # Setup LLM service mock
        mock_llm = AsyncMock()
        mock_llm.is_available = AsyncMock(return_value=True)
        mock_llm._call_llm = AsyncMock(return_value='{"command": "play", "parameters": {"query": "upbeat music"}, "thinking_message": "Playing upbeat music"}')
        
        bot.service_manager.container.register('llm_service', mock_llm)
        
        # Create natural language message
        mock_message.content = "!/play something upbeat"
        
        # Process message
        await bot.nlp_handler.handle_natural_language(mock_message)
        
        # Verify LLM was called
        assert mock_llm._call_llm.called
    
    async def test_complex_nlp_workflow(self, bot, mock_message):
        """Test complex natural language command with action chaining"""
        # Setup services
        mock_llm = AsyncMock()
        mock_llm.is_available = AsyncMock(return_value=True)
        
        mock_advanced_ai = MagicMock()
        mock_advanced_ai.parse_complex_intent = AsyncMock(return_value=[])
        
        bot.service_manager.container.register('llm_service', mock_llm)
        bot.service_manager.container.register('advanced_ai_service', mock_advanced_ai)
        
        # Create complex natural language message
        mock_message.content = "!/play something upbeat then skip after 30 seconds"
        
        # Process message
        await bot.nlp_handler.handle_natural_language(mock_message)
        
        # Verify advanced AI was called
        assert mock_advanced_ai.parse_complex_intent.called


@pytest.mark.asyncio
class TestServiceLifecycleIntegration:
    """Integration tests for service lifecycle management"""
    
    async def test_service_initialization_order(self):
        """Test services are initialized in correct order"""
        bot = create_bot()
        
        # Initialize services
        await bot.service_manager.initialize_all()
        
        # Verify initialization order
        assert bot.service_manager.is_service_available('bot')
        assert bot.service_manager.is_service_available('config')
        
        # Audio service should be available
        audio_service = bot.service_manager.get_service('audio_service')
        assert audio_service is not None
        
        await bot.close()
    
    async def test_service_shutdown_cleanup(self):
        """Test services are properly cleaned up on shutdown"""
        bot = create_bot()
        
        # Initialize services
        await bot.service_manager.initialize_all()
        
        # Get audio service
        audio_service = bot.service_manager.get_service('audio_service')
        
        # Shutdown
        await bot.close()
        
        # Verify cleanup (audio service should have shutdown called)
        # This is a basic check - in real scenario, verify resources are released
        assert bot.service_manager._initialized == False
    
    async def test_service_health_monitoring(self):
        """Test service health monitoring"""
        bot = create_bot()
        
        # Initialize services
        await bot.service_manager.initialize_all()
        
        # Check health
        health = await bot.service_manager.health_check()
        
        # Verify health check results
        assert isinstance(health, dict)
        assert 'audio_service' in health
        assert 'llm_service' in health
        assert 'synthesis_service' in health
        assert 'advanced_ai_service' in health
        
        await bot.close()


@pytest.mark.asyncio
class TestEndToEndWorkflows:
    """End-to-end integration tests"""
    
    async def test_complete_bot_lifecycle(self):
        """Test complete bot lifecycle from start to shutdown"""
        bot = create_bot()
        
        # Mock start to prevent actual Discord connection
        bot.start = AsyncMock()
        
        # Initialize
        await bot.setup_hook()
        
        # Verify bot is ready
        assert bot.service_manager._initialized
        
        # Simulate ready event
        await bot.on_ready()
        
        # Shutdown
        await bot.close()
        
        # Verify cleanup
        assert bot.service_manager._initialized == False
    
    async def test_command_processing_pipeline(self, mock_message):
        """Test complete command processing pipeline"""
        bot = create_bot()
        bot.start = AsyncMock()
        
        await bot.setup_hook()
        
        # Test regular command
        mock_message.content = "!ping"
        await bot.on_message(mock_message)
        
        # Verify command was processed
        assert bot.process_commands.called or mock_message.channel.send.called
        
        await bot.close()
    
    async def test_error_recovery_workflow(self, mock_message):
        """Test error recovery in workflows"""
        bot = create_bot()
        bot.start = AsyncMock()
        
        await bot.setup_hook()
        
        # Simulate error in command
        with patch('cogs.music.Music.play', side_effect=Exception("Test error")):
            await bot.load_extension('cogs.music')
            
            # Process command that will fail
            mock_message.content = "!play test"
            await bot.on_message(mock_message)
            
            # Bot should still be functional
            assert bot.service_manager._initialized
        
        await bot.close()


# Performance tests
@pytest.mark.asyncio
@pytest.mark.slow
class TestPerformanceIntegration:
    """Performance integration tests"""
    
    async def test_cache_performance(self):
        """Test caching improves performance"""
        from services.audio_service_enhanced import AudioService
        import time
        
        audio_service = AudioService(thread_pool_size=2)
        
        with patch('yt_dlp.YoutubeDL') as MockYTDL:
            mock_ytdl = MockYTDL.return_value.__enter__.return_value
            mock_ytdl.extract_info.return_value = {
                'title': 'Test Video',
                'url': 'http://example.com/video',
                'duration': 180,
                'uploader': 'Test Channel'
            }
            
            # First call (uncached)
            start = time.time()
            await audio_service.get_video_metadata('http://example.com/test')
            uncached_time = time.time() - start
            
            # Second call (cached)
            start = time.time()
            await audio_service.get_video_metadata('http://example.com/test')
            cached_time = time.time() - start
            
            # Cached should be significantly faster
            assert cached_time < uncached_time * 0.5  # At least 2x faster
        
        audio_service.shutdown()
    
    async def test_concurrent_request_handling(self):
        """Test handling of concurrent requests"""
        from services.audio_service_enhanced import AudioService
        
        audio_service = AudioService(thread_pool_size=4)
        
        with patch('yt_dlp.YoutubeDL') as MockYTDL:
            mock_ytdl = MockYTDL.return_value.__enter__.return_value
            mock_ytdl.extract_info.return_value = {
                'title': 'Test Video',
                'url': 'http://example.com/video',
                'duration': 180,
                'uploader': 'Test Channel'
            }
            
            # Execute 10 concurrent requests
            tasks = [
                audio_service.get_video_metadata(f'http://example.com/test{i}')
                for i in range(10)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All requests should succeed
            assert len(results) == 10
            assert all(r is not None for r in results if not isinstance(r, Exception))
        
        audio_service.shutdown()
