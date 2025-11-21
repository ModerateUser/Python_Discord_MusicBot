"""
Discord Music Bot with Integrated Web Dashboard
Runs both bot and dashboard in the same process using asyncio tasks
Provides real-time communication between components

FIX WEBUI #4: Complete integration of bot and dashboard
FIX INTEGRATION #1: Remove duplicate event handlers and API endpoints
FIX INTEGRATION #2: Connect WebSocket manager to dashboard bridge
"""
import asyncio
import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

# FastAPI imports
from fastapi import FastAPI
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import bot components
from core.bot_core import create_bot
from core.config import config
from utils.logger import setup_logger

# Import dashboard bridge
from services.dashboard_bridge import DashboardBridge, set_dashboard_bridge

# Import web dashboard app
from web_dashboard.app import app as dashboard_app, manager as websocket_manager, bot_state

# Setup logging
logger = setup_logger()


class IntegratedMusicBot:
    """
    Integrated Discord Music Bot with Web Dashboard
    Runs both components in the same process with real-time communication
    """
    
    def __init__(self):
        """Initialize integrated bot system"""
        self.bot = None
        self.dashboard_bridge = None
        self.dashboard_task = None
        self.bot_task = None
        self.uvicorn_server = None
        
    async def setup(self):
        """Setup bot and dashboard components"""
        logger.info("Setting up integrated bot system...")
        
        # Create bot instance
        self.bot = create_bot()
        
        # Create dashboard bridge
        self.dashboard_bridge = DashboardBridge(self.bot)
        set_dashboard_bridge(self.dashboard_bridge)
        
        # FIX INTEGRATION #2: Connect WebSocket manager to bridge
        self.dashboard_bridge.set_websocket_manager(websocket_manager)
        logger.info("✅ WebSocket manager connected to dashboard bridge")
        
        # Subscribe dashboard to bridge updates
        self.dashboard_bridge.subscribe(self._handle_bridge_update)
        
        # Register bot event handlers for dashboard
        self._register_bot_events()
        
        logger.info("✅ Integrated system setup complete")
    
    def _register_bot_events(self):
        """Register bot events for dashboard updates"""
        
        @self.bot.event
        async def on_ready():
            """Called when bot is ready"""
            # Call original on_ready
            if hasattr(self.bot, '_original_on_ready'):
                await self.bot._original_on_ready()
            
            # Update dashboard state
            bot_state['connected'] = True
            bot_state['status'] = 'online'
            bot_state['start_time'] = self.dashboard_bridge.start_time
            
            # Send initial status
            status = await self.dashboard_bridge.get_bot_status()
            await self._broadcast_to_dashboard('bot_ready', status.to_dict())
        
        @self.bot.event
        async def on_guild_join(guild):
            """Called when bot joins a guild"""
            self.dashboard_bridge.on_guild_join(guild)
        
        @self.bot.event
        async def on_guild_remove(guild):
            """Called when bot leaves a guild"""
            self.dashboard_bridge.on_guild_remove(guild)
        
        @self.bot.event
        async def on_voice_state_update(member, before, after):
            """Called when voice state changes"""
            # Call original handler
            if hasattr(self.bot, '_original_on_voice_state_update'):
                await self.bot._original_on_voice_state_update(member, before, after)
            
            # Update dashboard
            self.dashboard_bridge.on_voice_state_update(member, before, after)
    
    async def _handle_bridge_update(self, message: dict):
        """
        Handle updates from dashboard bridge
        
        Args:
            message: Update message
        """
        try:
            # Update bot_state
            if message['type'] == 'status_update':
                bot_state.update(message['data'])
            elif message['type'] == 'queue_update':
                guild_id = message['data']['guild_id']
                queue_info = await self.dashboard_bridge.get_guild_queue(guild_id)
                if queue_info:
                    bot_state['queues'][str(guild_id)] = queue_info.to_dict()
            
            # Broadcast to WebSocket clients (handled by bridge now)
            # No need to call websocket_manager.broadcast here - bridge does it
            
        except Exception as e:
            logger.error(f"Error handling bridge update: {e}", exc_info=True)
    
    async def _broadcast_to_dashboard(self, event_type: str, data: dict):
        """
        Broadcast event to dashboard WebSocket clients
        
        Args:
            event_type: Type of event
            data: Event data
        """
        try:
            await websocket_manager.broadcast({
                "type": event_type,
                "data": data,
                "timestamp": data.get('timestamp', asyncio.get_event_loop().time())
            })
        except Exception as e:
            logger.error(f"Error broadcasting to dashboard: {e}", exc_info=True)
    
    async def start_bot(self):
        """Start the Discord bot"""
        try:
            logger.info("Starting Discord bot...")
            await self.bot.start(config.token)
        except Exception as e:
            logger.error(f"Bot error: {e}", exc_info=True)
            raise
    
    async def start_dashboard(self):
        """Start the web dashboard"""
        try:
            logger.info("Starting web dashboard...")
            
            # Configure uvicorn
            config_dict = {
                "app": dashboard_app,
                "host": "0.0.0.0",
                "port": 8000,
                "log_level": "info",
                "access_log": False  # Reduce noise
            }
            
            # Create and run server
            self.uvicorn_server = uvicorn.Server(uvicorn.Config(**config_dict))
            await self.uvicorn_server.serve()
            
        except Exception as e:
            logger.error(f"Dashboard error: {e}", exc_info=True)
            raise
    
    async def run(self):
        """Run the integrated system"""
        await self.setup()
        
        # Start dashboard bridge
        await self.dashboard_bridge.start()
        
        # Create tasks for bot and dashboard
        self.bot_task = asyncio.create_task(self.start_bot())
        self.dashboard_task = asyncio.create_task(self.start_dashboard())
        
        logger.info("=" * 70)
        logger.info("🎵 Discord Music Bot with Web Dashboard")
        logger.info("=" * 70)
        logger.info(f"Dashboard URL: http://localhost:8000")
        logger.info(f"API Docs: http://localhost:8000/docs")
        logger.info(f"Health Check: http://localhost:8000/health")
        logger.info("=" * 70)
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 70)
        
        try:
            # Wait for both tasks
            await asyncio.gather(self.bot_task, self.dashboard_task)
        except asyncio.CancelledError:
            logger.info("Shutting down...")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown the integrated system"""
        logger.info("Shutting down integrated system...")
        
        # Stop dashboard bridge
        if self.dashboard_bridge:
            await self.dashboard_bridge.stop()
        
        # Cancel tasks
        if self.bot_task and not self.bot_task.done():
            self.bot_task.cancel()
            try:
                await self.bot_task
            except asyncio.CancelledError:
                pass
        
        if self.dashboard_task and not self.dashboard_task.done():
            self.dashboard_task.cancel()
            try:
                await self.dashboard_task
            except asyncio.CancelledError:
                pass
        
        # Close bot
        if self.bot and not self.bot.is_closed():
            await self.bot.close()
        
        # Stop uvicorn server
        if self.uvicorn_server:
            self.uvicorn_server.should_exit = True
        
        logger.info("✅ Shutdown complete")


# FIX INTEGRATION #1: Removed duplicate @dashboard_app.on_event("startup")
# The dashboard app now uses modern lifespan handler in web_dashboard/app.py
# and automatically connects to the bridge when available

# FIX INTEGRATION #1: Removed duplicate API endpoints
# All API endpoints are now defined in web_dashboard/app.py
# The following endpoints were removed from here:
# - POST /api/guild/{guild_id}/command
# - GET /api/guild/{guild_id}/queue
# - GET /api/status/live
# - GET /api/health/services


async def main():
    """Main entry point for integrated system"""
    integrated_bot = IntegratedMusicBot()
    
    try:
        await integrated_bot.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nSystem stopped by user")
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
