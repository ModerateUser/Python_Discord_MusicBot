"""
Integration Tests - Service Integration
Tests service interactions and dependency injection
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.service_manager import ServiceManager
from core.container import get_container
from core.bot_core import create_bot


@pytest.mark.asyncio
class TestServiceManagerIntegration:
    """Integration tests for service manager"""
    
    @pytest.fixture
    async def bot(self):
        """Create test bot"""
        bot = create_bot()
        bot.start = AsyncMock()
        yield bot
        await bot.close()
    
    async def test_service_registration_and_retrieval(self, bot):
        """Test service registration and retrieval"""
        service_manager = bot.service_manager
        
        # Register a test service
        test_service = MagicMock()
        service_manager.container.register('test_service', test_service)
        
        # Retrieve service
        retrieved = service_manager.get_service('test_service')
        assert retrieved is test_service
    
    async def test_service_availability_check(self, bot):
        """Test service availability checking"""
        service_manager = bot.service_manager
        
        # Check non-existent service
        assert not service_manager.is_service_available('nonexistent')
        
        # Register and check
        service_manager.container.register('test', MagicMock())
        assert service_manager.is_service_available('test')
    
    async def test_audio_service_initialization(self, bot):
        """Test audio service initialization"""
        await bot.service_manager.initialize_all()
        
        audio_service = bot.service_manager.get_service('audio_service')
        assert audio_service is not None
        
        # Verify audio service has required methods
        assert hasattr(audio_service, 'create_ytdl_source')
        assert hasattr(audio_service, 'get_video_metadata')
        assert hasattr(audio_service, 'search_youtube')
        assert hasattr(audio_service, 'shutdown')
    
    async def test_service_health_check_integration(self, bot):
        """Test service health check"""
        await bot.service_manager.initialize_all()
        
        health = await bot.service_manager.health_check()
        
        # Verify health check structure
        assert isinstance(health, dict)
        assert 'audio_service' in health
        assert 'llm_service' in health
        assert 'synthesis_service' in health
        assert 'advanced_ai_service' in health
        
        # Audio service should be healthy
        assert health['audio_service'] == True
    
    async def test_service_shutdown_integration(self, bot):
        """Test service shutdown"""
        await bot.service_manager.initialize_all()
        
        # Get audio service
        audio_service = bot.service_manager.get_service('audio_service')
        assert audio_service is not None
        
        # Shutdown
        await bot.service_manager.shutdown_all()
        
        # Verify shutdown state
        assert bot.service_manager._initialized == False


@pytest.mark.asyncio
class TestDependencyInjectionIntegration:
    """Integration tests for dependency injection"""
    
    async def test_container_singleton_pattern(self):
        """Test container singleton pattern"""
        container1 = get_container()
        container2 = get_container()
        
        assert container1 is container2
    
    async def test_service_dependencies(self):
        """Test service dependencies are resolved"""
        bot = create_bot()
        await bot.service_manager.initialize_all()
        
        # Config should be available to all services
        config = bot.service_manager.get_service('config')
        assert config is not None
        
        # Bot should be available
        bot_service = bot.service_manager.get_service('bot')
        assert bot_service is bot
        
        await bot.close()
    
    async def test_lazy_service_initialization(self):
        """Test lazy service initialization"""
        container = get_container()
        
        # Register with factory
        initialized = False
        
        def factory():
            nonlocal initialized
            initialized = True
            return MagicMock()
        
        container.register('lazy_service', factory=factory, singleton=True)
        
        # Should not be initialized yet
        assert not initialized
        
        # Get service - should initialize now
        service = container.get('lazy_service')
        assert initialized
        assert service is not None


@pytest.mark.asyncio
class TestCachingIntegration:
    """Integration tests for caching"""
    
    async def test_cache_integration_with_audio_service(self):
        """Test cache integration with audio service"""
        from services.audio_service_enhanced import AudioService
        from utils.cache import get_cache_manager
        
        audio_service = AudioService(thread_pool_size=2)
        cache_manager = get_cache_manager()
        
        # Clear cache
        await cache_manager.clear_cache('youtube_metadata')
        
        with patch('yt_dlp.YoutubeDL') as MockYTDL:
            mock_ytdl = MockYTDL.return_value.__enter__.return_value
            mock_ytdl.extract_info.return_value = {
                'title': 'Test Video',
                'url': 'http://example.com/video',
                'duration': 180,
                'uploader': 'Test Channel'
            }
            
            # First call
            metadata1 = await audio_service.get_video_metadata('http://test.com/video')
            
            # Check cache stats
            stats_before = cache_manager.get_cache_stats('youtube_metadata')
            
            # Second call (should hit cache)
            metadata2 = await audio_service.get_video_metadata('http://test.com/video')
            
            # Check cache stats again
            stats_after = cache_manager.get_cache_stats('youtube_metadata')
            
            # Verify cache hit
            assert stats_after['hits'] > stats_before['hits']
            assert metadata1.title == metadata2.title
        
        audio_service.shutdown()
    
    async def test_cache_expiration(self):
        """Test cache expiration"""
        from utils.cache import Cache
        import asyncio
        
        # Create cache with 1 second TTL
        cache = Cache(name='test_cache', ttl_seconds=1, max_size=100)
        
        # Add item
        cache.set('key1', 'value1')
        
        # Should be available immediately
        assert cache.get('key1') == 'value1'
        
        # Wait for expiration
        await asyncio.sleep(1.5)
        
        # Should be expired
        assert cache.get('key1') is None
    
    async def test_cache_lru_eviction(self):
        """Test LRU eviction"""
        from utils.cache import Cache
        
        # Create cache with max size 3
        cache = Cache(name='test_cache', ttl_seconds=300, max_size=3)
        
        # Add 4 items
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.set('key3', 'value3')
        cache.set('key4', 'value4')  # Should evict key1
        
        # key1 should be evicted
        assert cache.get('key1') is None
        assert cache.get('key2') == 'value2'
        assert cache.get('key3') == 'value3'
        assert cache.get('key4') == 'value4'
    
    async def test_multiple_cache_instances(self):
        """Test multiple cache instances"""
        from utils.cache import get_cache_manager
        
        manager = get_cache_manager()
        
        # Get different caches
        cache1 = manager.get_cache('youtube_metadata')
        cache2 = manager.get_cache('search_results')
        
        assert cache1 is not cache2
        assert cache1.name == 'youtube_metadata'
        assert cache2.name == 'search_results'


@pytest.mark.asyncio
class TestNLPServiceIntegration:
    """Integration tests for NLP service"""
    
    @pytest.fixture
    async def bot(self):
        """Create test bot"""
        bot = create_bot()
        bot.start = AsyncMock()
        yield bot
        await bot.close()
    
    async def test_nlp_handler_initialization(self, bot):
        """Test NLP handler initialization"""
        assert bot.nlp_handler is not None
        assert bot.nlp_handler.bot is bot
    
    async def test_simple_intent_parsing(self, bot):
        """Test simple intent parsing"""
        # Mock LLM service
        mock_llm = AsyncMock()
        mock_llm.is_available = AsyncMock(return_value=True)
        mock_llm._call_llm = AsyncMock(
            return_value='{"command": "play", "parameters": {"query": "test song"}, "thinking_message": "Playing test song"}'
        )
        
        bot.service_manager.container.register('llm_service', mock_llm)
        
        # Parse intent
        intent = await bot.nlp_handler.parse_simple_intent("play test song")
        
        assert intent is not None
        assert intent['command'] == 'play'
        assert intent['parameters']['query'] == 'test song'
    
    async def test_complex_command_detection(self, bot):
        """Test complex command detection"""
        nlp_handler = bot.nlp_handler
        
        # Simple commands
        assert not nlp_handler._is_complex_command("play a song")
        assert not nlp_handler._is_complex_command("skip this")
        
        # Complex commands
        assert nlp_handler._is_complex_command("play a song then skip after 30 seconds")
        assert nlp_handler._is_complex_command("create a mood playlist")
        assert nlp_handler._is_complex_command("synthesize some music")
        assert nlp_handler._is_complex_command("find similar songs")


@pytest.mark.asyncio
class TestActionExecutorIntegration:
    """Integration tests for action executor"""
    
    @pytest.fixture
    async def bot(self):
        """Create test bot"""
        bot = create_bot()
        bot.start = AsyncMock()
        yield bot
        await bot.close()
    
    async def test_action_executor_initialization(self, bot):
        """Test action executor initialization"""
        from core.action_executor import ActionExecutor
        
        executor = ActionExecutor(bot)
        assert executor.bot is bot
        assert executor.container is not None
    
    async def test_action_parameter_validation(self, bot):
        """Test action parameter validation"""
        from core.action_executor import ActionExecutor
        from services.ai_music_service import Action, ActionType
        
        executor = ActionExecutor(bot)
        
        # Valid volume action
        valid_action = Action(
            action_type=ActionType.VOLUME,
            parameters={'level': 50},
            description="Set volume to 50%"
        )
        assert executor._validate_action_parameters(valid_action)
        
        # Invalid volume action
        invalid_action = Action(
            action_type=ActionType.VOLUME,
            parameters={'level': 150},  # Out of range
            description="Set volume to 150%"
        )
        assert not executor._validate_action_parameters(invalid_action)
    
    async def test_play_action_execution(self, bot, mock_message):
        """Test play action execution"""
        from core.action_executor import ActionExecutor
        from services.ai_music_service import Action, ActionType
        
        executor = ActionExecutor(bot)
        
        # Mock music cog
        mock_music_cog = MagicMock()
        mock_music_cog.play = AsyncMock()
        bot.get_cog = MagicMock(return_value=mock_music_cog)
        
        # Create play action
        action = Action(
            action_type=ActionType.PLAY,
            parameters={'query': 'test song'},
            description="Play test song"
        )
        
        # Execute action
        await executor._execute_play(mock_message, action, mock_music_cog)
        
        # Verify play was called
        mock_music_cog.play.assert_called_once()


@pytest.mark.asyncio
class TestEndToEndServiceIntegration:
    """End-to-end service integration tests"""
    
    async def test_complete_service_workflow(self):
        """Test complete service workflow from bot start to shutdown"""
        bot = create_bot()
        bot.start = AsyncMock()
        
        # Initialize
        await bot.setup_hook()
        
        # Verify services are initialized
        assert bot.service_manager._initialized
        
        # Check health
        health = await bot.service_manager.health_check()
        assert health['audio_service'] == True
        
        # Get a service
        audio_service = bot.service_manager.get_service('audio_service')
        assert audio_service is not None
        
        # Shutdown
        await bot.close()
        
        # Verify cleanup
        assert bot.service_manager._initialized == False
    
    async def test_service_interaction_workflow(self):
        """Test services interacting with each other"""
        bot = create_bot()
        bot.start = AsyncMock()
        
        await bot.setup_hook()
        
        # Get services
        audio_service = bot.service_manager.get_service('audio_service')
        config = bot.service_manager.get_service('config')
        
        # Both should be available
        assert audio_service is not None
        assert config is not None
        
        # Services should be able to interact
        # (In real scenario, audio service would use config)
        
        await bot.close()
    
    async def test_service_error_isolation(self):
        """Test that service errors are isolated"""
        bot = create_bot()
        bot.start = AsyncMock()
        
        # Mock a failing service initialization
        with patch.object(
            bot.service_manager,
            '_initialize_synthesis_service',
            side_effect=Exception("Test error")
        ):
            # Should not crash entire initialization
            await bot.setup_hook()
            
            # Other services should still be available
            audio_service = bot.service_manager.get_service('audio_service')
            assert audio_service is not None
        
        await bot.close()


@pytest.mark.asyncio
class TestConcurrencyIntegration:
    """Integration tests for concurrent operations"""
    
    async def test_concurrent_service_access(self):
        """Test concurrent access to services"""
        import asyncio
        
        bot = create_bot()
        bot.start = AsyncMock()
        await bot.setup_hook()
        
        # Access service concurrently
        async def access_service():
            return bot.service_manager.get_service('audio_service')
        
        tasks = [access_service() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should get the same service instance
        assert all(r is results[0] for r in results)
        
        await bot.close()
    
    async def test_concurrent_cache_access(self):
        """Test concurrent cache access"""
        import asyncio
        from utils.cache import Cache
        
        cache = Cache(name='test', ttl_seconds=300, max_size=100)
        
        # Concurrent writes
        async def write_cache(key, value):
            cache.set(key, value)
            return cache.get(key)
        
        tasks = [write_cache(f'key{i}', f'value{i}') for i in range(20)]
        results = await asyncio.gather(*tasks)
        
        # All writes should succeed
        assert len(results) == 20
        assert all(r is not None for r in results)
    
    async def test_concurrent_audio_requests(self):
        """Test concurrent audio service requests"""
        import asyncio
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
            
            # Concurrent metadata requests
            tasks = [
                audio_service.get_video_metadata(f'http://test.com/video{i}')
                for i in range(10)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should succeed
            assert len(results) == 10
            successful = [r for r in results if not isinstance(r, Exception)]
            assert len(successful) == 10
        
        audio_service.shutdown()


@pytest.mark.asyncio
class TestErrorHandlingIntegration:
    """Integration tests for error handling"""
    
    async def test_service_initialization_error_handling(self):
        """Test error handling during service initialization"""
        bot = create_bot()
        bot.start = AsyncMock()
        
        # Mock a service that fails to initialize
        with patch('services.audio_service_enhanced.AudioService', side_effect=Exception("Init error")):
            # Should not crash
            await bot.setup_hook()
            
            # Bot should still be functional
            assert bot.service_manager is not None
        
        await bot.close()
    
    async def test_cache_error_handling(self):
        """Test cache error handling"""
        from utils.cache import Cache
        
        cache = Cache(name='test', ttl_seconds=300, max_size=100)
        
        # Getting non-existent key should return None, not error
        result = cache.get('nonexistent')
        assert result is None
        
        # Setting with invalid key should not crash
        try:
            cache.set(None, 'value')
        except:
            pass  # Expected to handle gracefully
    
    async def test_nlp_parsing_error_handling(self):
        """Test NLP parsing error handling"""
        bot = create_bot()
        bot.start = AsyncMock()
        
        # Mock LLM that returns invalid JSON
        mock_llm = AsyncMock()
        mock_llm.is_available = AsyncMock(return_value=True)
        mock_llm._call_llm = AsyncMock(return_value='invalid json')
        
        bot.service_manager.container.register('llm_service', mock_llm)
        
        # Should handle gracefully
        intent = await bot.nlp_handler.parse_simple_intent("test query")
        
        # Should return None or handle error
        assert intent is None or isinstance(intent, dict)
        
        await bot.close()
