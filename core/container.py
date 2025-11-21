"""
Dependency Injection Container for Discord Music Bot
Replaces global state with proper service management
"""
import logging
from typing import Dict, Any, Optional, Callable, TypeVar
from threading import Lock
import asyncio

logger = logging.getLogger('discord_bot')

T = TypeVar('T')


class ServiceContainer:
    """
    Dependency injection container for managing service instances
    
    Features:
    - Thread-safe service registration and retrieval
    - Lazy initialization support
    - Singleton pattern enforcement
    - Service lifecycle management
    - Clear dependency graph
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, bool] = {}
        self._lock = Lock()
        self._initialized: Dict[str, bool] = {}
        
        logger.info("Service container initialized")
    
    def register(
        self, 
        name: str, 
        service: Any = None,
        factory: Optional[Callable] = None,
        singleton: bool = True
    ) -> None:
        """
        Register a service in the container
        
        Args:
            name: Service identifier
            service: Service instance (if already created)
            factory: Factory function to create service (for lazy init)
            singleton: Whether to reuse the same instance
            
        Example:
            container.register('audio_service', audio_service)
            container.register('llm_service', factory=create_llm_service, singleton=True)
        """
        with self._lock:
            if service is not None:
                self._services[name] = service
                self._initialized[name] = True
                logger.debug(f"Registered service: {name}")
            elif factory is not None:
                self._factories[name] = factory
                self._singletons[name] = singleton
                self._initialized[name] = False
                logger.debug(f"Registered factory for: {name} (singleton={singleton})")
            else:
                raise ValueError(f"Must provide either service or factory for {name}")
    
    def get(self, name: str) -> Optional[Any]:
        """
        Get a service from the container
        
        Args:
            name: Service identifier
            
        Returns:
            Service instance or None if not found
            
        Example:
            audio_service = container.get('audio_service')
        """
        with self._lock:
            # Return existing service if available
            if name in self._services:
                return self._services[name]
            
            # Create service from factory if available
            if name in self._factories:
                factory = self._factories[name]
                is_singleton = self._singletons.get(name, True)
                
                try:
                    logger.debug(f"Creating service from factory: {name}")
                    service = factory()
                    
                    if is_singleton:
                        self._services[name] = service
                        self._initialized[name] = True
                    
                    return service
                    
                except Exception as e:
                    logger.error(f"Error creating service {name}: {e}", exc_info=True)
                    return None
            
            logger.warning(f"Service not found: {name}")
            return None
    
    def get_or_raise(self, name: str) -> Any:
        """
        Get a service or raise exception if not found
        
        Args:
            name: Service identifier
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If service not found
        """
        service = self.get(name)
        if service is None:
            raise KeyError(f"Service not found: {name}")
        return service
    
    def has(self, name: str) -> bool:
        """
        Check if service is registered
        
        Args:
            name: Service identifier
            
        Returns:
            True if service exists
        """
        with self._lock:
            return name in self._services or name in self._factories
    
    def is_initialized(self, name: str) -> bool:
        """
        Check if service has been initialized
        
        Args:
            name: Service identifier
            
        Returns:
            True if service is initialized
        """
        with self._lock:
            return self._initialized.get(name, False)
    
    def unregister(self, name: str) -> None:
        """
        Remove a service from the container
        
        Args:
            name: Service identifier
        """
        with self._lock:
            if name in self._services:
                del self._services[name]
                logger.debug(f"Unregistered service: {name}")
            
            if name in self._factories:
                del self._factories[name]
            
            if name in self._singletons:
                del self._singletons[name]
            
            if name in self._initialized:
                del self._initialized[name]
    
    def clear(self) -> None:
        """Clear all services from container"""
        with self._lock:
            self._services.clear()
            self._factories.clear()
            self._singletons.clear()
            self._initialized.clear()
            logger.info("Service container cleared")
    
    def list_services(self) -> list[str]:
        """
        Get list of all registered service names
        
        Returns:
            List of service names
        """
        with self._lock:
            all_services = set(self._services.keys()) | set(self._factories.keys())
            return sorted(all_services)
    
    def get_service_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a service
        
        Args:
            name: Service identifier
            
        Returns:
            Dictionary with service info or None
        """
        with self._lock:
            if not self.has(name):
                return None
            
            info = {
                'name': name,
                'initialized': self._initialized.get(name, False),
                'is_singleton': self._singletons.get(name, True),
                'has_instance': name in self._services,
                'has_factory': name in self._factories
            }
            
            if name in self._services:
                service = self._services[name]
                info['type'] = type(service).__name__
            
            return info
    
    async def initialize_async_service(
        self, 
        name: str, 
        factory: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Initialize an async service
        
        Args:
            name: Service identifier
            factory: Async factory function
            *args: Positional arguments for factory
            **kwargs: Keyword arguments for factory
            
        Returns:
            Initialized service
        """
        try:
            logger.debug(f"Initializing async service: {name}")
            service = await factory(*args, **kwargs)
            
            with self._lock:
                self._services[name] = service
                self._initialized[name] = True
            
            logger.info(f"Async service initialized: {name}")
            return service
            
        except Exception as e:
            logger.error(f"Error initializing async service {name}: {e}", exc_info=True)
            raise
    
    async def shutdown_async_service(self, name: str) -> None:
        """
        Shutdown an async service gracefully
        
        Args:
            name: Service identifier
        """
        service = self.get(name)
        if service is None:
            return
        
        try:
            # Check if service has shutdown method
            if hasattr(service, 'shutdown'):
                logger.debug(f"Shutting down service: {name}")
                if asyncio.iscoroutinefunction(service.shutdown):
                    await service.shutdown()
                else:
                    service.shutdown()
            
            # Check if service has close method
            elif hasattr(service, 'close'):
                logger.debug(f"Closing service: {name}")
                if asyncio.iscoroutinefunction(service.close):
                    await service.close()
                else:
                    service.close()
            
            self.unregister(name)
            logger.info(f"Service shutdown complete: {name}")
            
        except Exception as e:
            logger.error(f"Error shutting down service {name}: {e}", exc_info=True)
    
    async def shutdown_all(self) -> None:
        """Shutdown all services gracefully"""
        logger.info("Shutting down all services...")
        
        service_names = self.list_services()
        for name in service_names:
            await self.shutdown_async_service(name)
        
        self.clear()
        logger.info("All services shut down")
    
    def __repr__(self) -> str:
        """String representation of container"""
        services = self.list_services()
        return f"ServiceContainer(services={len(services)}: {', '.join(services)})"


# Global container instance (singleton pattern)
_container: Optional[ServiceContainer] = None
_container_lock = Lock()


def get_container() -> ServiceContainer:
    """
    Get the global service container instance
    
    Returns:
        ServiceContainer singleton
    """
    global _container
    
    if _container is None:
        with _container_lock:
            if _container is None:
                _container = ServiceContainer()
    
    return _container


def reset_container() -> None:
    """
    Reset the global container (mainly for testing)
    """
    global _container
    
    with _container_lock:
        if _container is not None:
            _container.clear()
        _container = None


# Convenience functions
def register_service(name: str, service: Any = None, **kwargs) -> None:
    """Register a service in the global container"""
    container = get_container()
    container.register(name, service, **kwargs)


def get_service(name: str) -> Optional[Any]:
    """Get a service from the global container"""
    container = get_container()
    return container.get(name)


def has_service(name: str) -> bool:
    """Check if service exists in global container"""
    container = get_container()
    return container.has(name)
