"""
Dashboard Bridge Service
Provides real-time communication between Discord bot and web dashboard
Uses asyncio for same-process integration with minimal overhead

FIX WEBUI #3: Complete bot-dashboard integration
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


@dataclass
class BotStatus:
    """Bot status information"""
    connected: bool
    status: str
    guilds: List[Dict[str, Any]]
    uptime: Optional[str]
    start_time: datetime
    version: str = "1.0.0"
    latency: float = 0.0
    total_users: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        return data


@dataclass
class QueueInfo:
    """Queue information for a guild"""
    guild_id: int
    guild_name: str
    current_song: Optional[Dict[str, Any]]
    queue: List[Dict[str, Any]]
    is_playing: bool
    is_paused: bool
    volume: float
    loop_mode: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class DashboardBridge:
    """
    Bridge service between Discord bot and web dashboard
    Provides real-time state synchronization and event broadcasting
    """
    
    def __init__(self, bot: commands.Bot):
        """
        Initialize dashboard bridge
        
        Args:
            bot: Discord bot instance
        """
        self.bot = bot
        self.start_time = datetime.now()
        self._subscribers: List[Callable] = []
        self._state_cache: Dict[str, Any] = {}
        self._update_task: Optional[asyncio.Task] = None
        
        logger.info("Dashboard Bridge initialized")
    
    async def start(self):
        """Start the bridge service"""
        logger.info("Starting Dashboard Bridge...")
        self._update_task = asyncio.create_task(self._periodic_update())
        logger.info("✅ Dashboard Bridge started")
    
    async def stop(self):
        """Stop the bridge service"""
        logger.info("Stopping Dashboard Bridge...")
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        logger.info("✅ Dashboard Bridge stopped")
    
    def subscribe(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Subscribe to state updates
        
        Args:
            callback: Async function to call with state updates
        """
        self._subscribers.append(callback)
        logger.debug(f"New subscriber added. Total: {len(self._subscribers)}")
    
    def unsubscribe(self, callback: Callable):
        """
        Unsubscribe from state updates
        
        Args:
            callback: Callback to remove
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            logger.debug(f"Subscriber removed. Total: {len(self._subscribers)}")
    
    async def _broadcast_update(self, update_type: str, data: Dict[str, Any]):
        """
        Broadcast update to all subscribers
        
        Args:
            update_type: Type of update
            data: Update data
        """
        message = {
            "type": update_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Call all subscribers
        for callback in self._subscribers[:]:  # Copy list to avoid modification during iteration
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except Exception as e:
                logger.error(f"Error in subscriber callback: {e}", exc_info=True)
    
    async def _periodic_update(self):
        """Periodically update and broadcast bot state"""
        while True:
            try:
                await asyncio.sleep(5)  # Update every 5 seconds
                
                # Get current state
                state = await self.get_bot_status()
                
                # Broadcast if changed
                if state != self._state_cache.get('bot_status'):
                    self._state_cache['bot_status'] = state
                    await self._broadcast_update('status_update', state.to_dict())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic update: {e}", exc_info=True)
    
    async def get_bot_status(self) -> BotStatus:
        """
        Get current bot status
        
        Returns:
            BotStatus object
        """
        # Calculate uptime
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        uptime_str = f"{hours}h {minutes}m"
        
        # Get guild information
        guilds = []
        total_users = 0
        for guild in self.bot.guilds:
            guilds.append({
                "id": guild.id,
                "name": guild.name,
                "member_count": guild.member_count,
                "icon_url": str(guild.icon.url) if guild.icon else None
            })
            total_users += guild.member_count
        
        # Determine status
        if self.bot.is_ready():
            status = "online"
        elif self.bot.is_closed():
            status = "offline"
        else:
            status = "connecting"
        
        return BotStatus(
            connected=self.bot.is_ready(),
            status=status,
            guilds=guilds,
            uptime=uptime_str,
            start_time=self.start_time,
            latency=round(self.bot.latency * 1000, 2),
            total_users=total_users
        )
    
    async def get_guild_queue(self, guild_id: int) -> Optional[QueueInfo]:
        """
        Get queue information for a guild
        
        Args:
            guild_id: Guild ID
            
        Returns:
            QueueInfo object or None if not found
        """
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return None
        
        # Get music cog
        music_cog = self.bot.get_cog('Music')
        if not music_cog:
            return None
        
        # Get voice client
        voice_client = guild.voice_client
        if not voice_client:
            return None
        
        # Get queue manager
        queue_manager_cog = self.bot.get_cog('QueueManager')
        if not queue_manager_cog:
            return None
        
        try:
            # Get queue data
            queue_data = queue_manager_cog.get_queue(guild_id)
            if not queue_data:
                return None
            
            # Get current song
            current_song = None
            if hasattr(voice_client, 'source') and voice_client.source:
                current_song = {
                    "title": getattr(voice_client.source, 'title', 'Unknown'),
                    "url": getattr(voice_client.source, 'url', None),
                    "duration": getattr(voice_client.source, 'duration', 0),
                    "requester": getattr(voice_client.source, 'requester', 'Unknown')
                }
            
            # Get queue items
            queue_items = []
            for item in queue_data.get('queue', []):
                queue_items.append({
                    "title": item.get('title', 'Unknown'),
                    "url": item.get('url', None),
                    "duration": item.get('duration', 0),
                    "requester": item.get('requester', 'Unknown')
                })
            
            return QueueInfo(
                guild_id=guild_id,
                guild_name=guild.name,
                current_song=current_song,
                queue=queue_items,
                is_playing=voice_client.is_playing(),
                is_paused=voice_client.is_paused(),
                volume=queue_data.get('volume', 1.0),
                loop_mode=queue_data.get('loop_mode', 'off')
            )
        except Exception as e:
            logger.error(f"Error getting queue for guild {guild_id}: {e}", exc_info=True)
            return None
    
    async def get_all_queues(self) -> List[QueueInfo]:
        """
        Get queue information for all guilds
        
        Returns:
            List of QueueInfo objects
        """
        queues = []
        for guild in self.bot.guilds:
            queue_info = await self.get_guild_queue(guild.id)
            if queue_info:
                queues.append(queue_info)
        return queues
    
    async def execute_command(self, guild_id: int, command: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a bot command from the dashboard
        
        Args:
            guild_id: Guild ID
            command: Command name
            **kwargs: Command arguments
            
        Returns:
            Result dictionary
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return {"success": False, "error": "Guild not found"}
            
            # Get voice client
            voice_client = guild.voice_client
            if not voice_client and command not in ['join', 'play']:
                return {"success": False, "error": "Bot not in voice channel"}
            
            # Execute command
            if command == 'pause':
                if voice_client and voice_client.is_playing():
                    voice_client.pause()
                    await self._broadcast_update('command_executed', {
                        "guild_id": guild_id,
                        "command": "pause"
                    })
                    return {"success": True, "message": "Playback paused"}
                return {"success": False, "error": "Nothing is playing"}
            
            elif command == 'resume':
                if voice_client and voice_client.is_paused():
                    voice_client.resume()
                    await self._broadcast_update('command_executed', {
                        "guild_id": guild_id,
                        "command": "resume"
                    })
                    return {"success": True, "message": "Playback resumed"}
                return {"success": False, "error": "Nothing is paused"}
            
            elif command == 'skip':
                if voice_client and voice_client.is_playing():
                    voice_client.stop()
                    await self._broadcast_update('command_executed', {
                        "guild_id": guild_id,
                        "command": "skip"
                    })
                    return {"success": True, "message": "Song skipped"}
                return {"success": False, "error": "Nothing is playing"}
            
            elif command == 'stop':
                if voice_client:
                    voice_client.stop()
                    await voice_client.disconnect()
                    await self._broadcast_update('command_executed', {
                        "guild_id": guild_id,
                        "command": "stop"
                    })
                    return {"success": True, "message": "Playback stopped"}
                return {"success": False, "error": "Bot not in voice channel"}
            
            elif command == 'volume':
                volume = kwargs.get('volume', 1.0)
                if voice_client and hasattr(voice_client, 'source'):
                    if hasattr(voice_client.source, 'volume'):
                        voice_client.source.volume = volume
                        await self._broadcast_update('command_executed', {
                            "guild_id": guild_id,
                            "command": "volume",
                            "volume": volume
                        })
                        return {"success": True, "message": f"Volume set to {int(volume * 100)}%"}
                return {"success": False, "error": "Cannot change volume"}
            
            else:
                return {"success": False, "error": f"Unknown command: {command}"}
        
        except Exception as e:
            logger.error(f"Error executing command {command}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def get_service_health(self) -> Dict[str, bool]:
        """
        Get health status of all services
        
        Returns:
            Dictionary mapping service names to health status
        """
        health = {
            "bot": self.bot.is_ready(),
            "dashboard_bridge": True
        }
        
        # Check service manager if available
        if hasattr(self.bot, 'service_manager'):
            try:
                service_health = await self.bot.service_manager.health_check()
                health.update(service_health)
            except Exception as e:
                logger.error(f"Error checking service health: {e}")
        
        return health
    
    def on_guild_join(self, guild: discord.Guild):
        """Called when bot joins a guild"""
        asyncio.create_task(self._broadcast_update('guild_join', {
            "guild_id": guild.id,
            "guild_name": guild.name,
            "member_count": guild.member_count
        }))
    
    def on_guild_remove(self, guild: discord.Guild):
        """Called when bot leaves a guild"""
        asyncio.create_task(self._broadcast_update('guild_remove', {
            "guild_id": guild.id,
            "guild_name": guild.name
        }))
    
    def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Called when voice state changes"""
        if member.id == self.bot.user.id:
            asyncio.create_task(self._broadcast_update('voice_state_update', {
                "guild_id": member.guild.id,
                "connected": after.channel is not None,
                "channel_name": after.channel.name if after.channel else None
            }))
    
    def on_track_start(self, guild_id: int, track_info: Dict[str, Any]):
        """Called when a track starts playing"""
        asyncio.create_task(self._broadcast_update('track_start', {
            "guild_id": guild_id,
            "track": track_info
        }))
    
    def on_track_end(self, guild_id: int):
        """Called when a track ends"""
        asyncio.create_task(self._broadcast_update('track_end', {
            "guild_id": guild_id
        }))
    
    def on_queue_update(self, guild_id: int):
        """Called when queue is updated"""
        asyncio.create_task(self._broadcast_update('queue_update', {
            "guild_id": guild_id
        }))


# Global instance (will be set by bot)
_bridge_instance: Optional[DashboardBridge] = None


def get_dashboard_bridge() -> Optional[DashboardBridge]:
    """
    Get the global dashboard bridge instance
    
    Returns:
        DashboardBridge instance or None
    """
    return _bridge_instance


def set_dashboard_bridge(bridge: DashboardBridge):
    """
    Set the global dashboard bridge instance
    
    Args:
        bridge: DashboardBridge instance
    """
    global _bridge_instance
    _bridge_instance = bridge
    logger.info("Global dashboard bridge instance set")
