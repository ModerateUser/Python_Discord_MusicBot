"""
Service Manager - Manages service lifecycle and initialization
Handles dependency injection and service health checks
"""
import logging
from typing import Optional, Dict, Any
from core.container import get_container
from core.config import config

logger = logging.getLogger(__name__)


class ServiceManager:
    """
    Manages the lifecycle of all bot services
    Uses dependency injection container for service management
    """
    
    def __init__(self, bot):
        """
        Initialize service manager
        
        Args:
            bot: Discord bot instance
        """
        self.bot = bot
        self.container = get_container()
        self._initialized = False
    
    async def initialize_all(self) -> None:
        """Initialize all services in the correct order"""
        if self._initialized:
            logger.warning("Services already initialized")
            return
        
        logger.info("Initializing services...")
        
        # Register bot instance
        self.container.register('bot', self.bot)
        self.container.register('config', config)
        
        # Initialize core services
        await self._initialize_audio_service()
        await self._initialize_llm_service()
        await self._initialize_synthesis_service()
        await self._initialize_advanced_ai_service()
        
        self._initialized = True
        logger.info("✅ All services initialized")
    
    async def _initialize_audio_service(self) -> None:
        """Initialize enhanced audio service"""
        try:
            from services.audio_service_enhanced import AudioService
            
            audio_service = AudioService(thread_pool_size=4)
            self.container.register('audio_service', audio_service)
            logger.info("✅ Audio service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize audio service: {e}", exc_info=True)
    
    async def _initialize_llm_service(self) -> None:
        """Initialize LLM service from AI cog"""
        try:
            ai_cog = self.bot.get_cog('AI Music')
            if ai_cog and hasattr(ai_cog, 'llm'):
                self.container.register('llm_service', ai_cog.llm)
                logger.info("✅ LLM service registered")
            else:
                logger.info("⚠️ LLM service not available")
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}", exc_info=True)
    
    async def _initialize_synthesis_service(self) -> None:
        """Initialize music synthesis service"""
        try:
            from services.music_synthesis_service import create_music_synthesis_service
            
            ai_cog = self.bot.get_cog('AI Music')
            llm_service = ai_cog.llm if ai_cog else None
            
            config_dict = config.to_dict()
            synthesis_service = create_music_synthesis_service(config_dict, llm_service)
            
            if await synthesis_service.is_available():
                self.container.register('synthesis_service', synthesis_service)
                logger.info(f'✅ Music Synthesis Service initialized (Backend: {synthesis_service.backend.value})')
            else:
                logger.info('⚠️ Music synthesis disabled (check config.json)')
        except ImportError as e:
            logger.error(f"Failed to import music synthesis service: {e}")
        except AttributeError as e:
            logger.error(f'Configuration error in music synthesis: {e}')
            logger.error('Make sure config.json has proper music_synthesis section')
        except Exception as e:
            logger.error(f'Unexpected error initializing music synthesis: {e}', exc_info=True)
    
    async def _initialize_advanced_ai_service(self) -> None:
        """Initialize advanced AI music service"""
        try:
            llm_service = self.container.get('llm_service')
            if not llm_service or not await llm_service.is_available():
                logger.info('⚠️ Advanced AI features unavailable (LLM not loaded)')
                return
            
            from services.ai_music_service import create_advanced_ai_service
            
            synthesis_service = self.container.get('synthesis_service')
            advanced_ai_service = create_advanced_ai_service(llm_service, synthesis_service)
            
            self.container.register('advanced_ai_service', advanced_ai_service)
            logger.info('✅ Advanced AI Music Service initialized')
        except ImportError as e:
            logger.error(f"Failed to import advanced AI service: {e}")
        except Exception as e:
            logger.error(f"Error initializing advanced AI service: {e}", exc_info=True)
    
    def get_service(self, name: str) -> Optional[Any]:
        """
        Get a service by name
        
        Args:
            name: Service name
            
        Returns:
            Service instance or None if not found
        """
        try:
            return self.container.get(name)
        except KeyError:
            logger.warning(f"Service not found: {name}")
            return None
    
    def is_service_available(self, name: str) -> bool:
        """
        Check if a service is available
        
        Args:
            name: Service name
            
        Returns:
            True if service is available
        """
        return self.container.has(name)
    
    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of all services
        
        Returns:
            Dictionary mapping service names to health status
        """
        health = {}
        
        # Check audio service
        audio_service = self.get_service('audio_service')
        health['audio_service'] = audio_service is not None
        
        # Check LLM service
        llm_service = self.get_service('llm_service')
        if llm_service:
            health['llm_service'] = await llm_service.is_available()
        else:
            health['llm_service'] = False
        
        # Check synthesis service
        synthesis_service = self.get_service('synthesis_service')
        if synthesis_service:
            health['synthesis_service'] = await synthesis_service.is_available()
        else:
            health['synthesis_service'] = False
        
        # Check advanced AI service
        health['advanced_ai_service'] = self.is_service_available('advanced_ai_service')
        
        return health
    
    async def shutdown_all(self) -> None:
        """Shutdown all services gracefully"""
        logger.info("Shutting down services...")
        
        # Shutdown audio service
        audio_service = self.get_service('audio_service')
        if audio_service and hasattr(audio_service, 'shutdown'):
            try:
                audio_service.shutdown()
                logger.info("✅ Audio service shutdown")
            except Exception as e:
                logger.error(f"Error shutting down audio service: {e}")
        
        # Shutdown container
        await self.container.shutdown_all()
        
        self._initialized = False
        logger.info("✅ All services shutdown")
