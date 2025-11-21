"""
Dashboard Bridge Service - PHASE 1 REFACTORED
Provides real-time communication between Discord bot and web dashboard
Uses asyncio for same-process integration with minimal overhead

FIX WEBUI #3: Complete bot-dashboard integration
PHASE 1 TASK 1.1: Real Queue Integration - IMPLEMENTED
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
    loop_mode: bool
    queue_length: int
    voice_channel: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class DashboardBridge:
    """
    Bridge service between Discord bot and web dashboard
    Provides real-time state synchronization and event broadcasting
    
    PHASE 1 TASK 1.1: Real Queue Integration - IMPLEMENTED
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
        self.websocket_manager = None  # Will be set by dashboard app
        
        logger.info("Dashboard Bridge initialized")
    
    def set_websocket_manager(self, manager):
        """
        Set the WebSocket manager for broadcasting updates
        
        Args:
            manager: WebSocket connection manager from dashboard app
        """
        self.websocket_manager = manager
        logger.info("WebSocket manager registered with dashboard bridge")
    
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
        Broadcast update to all subscribers and WebSocket clients
        
        Args:
            update_type: Type of update
            data: Update data
        """
        message = {
            "type": update_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Broadcast to WebSocket clients if manager is available
        if self.websocket_manager:
            try:
                await self.websocket_manager.broadcast(message)
                logger.debug(f"Broadcast {update_type} to WebSocket clients")
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}", exc_info=True)
        
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
    
    def get_guilds(self) -> List[Dict[str, Any]]:
        """
        Get list of all guilds the bot is in
        
        Returns:
            List of guild information dictionaries
        """
        guilds = []
        for guild in self.bot.guilds:
            # Check if bot is in voice channel
            voice_client = guild.voice_client
            in_voice = voice_client is not None
            voice_channel_name = voice_client.channel.name if voice_client else None
            
            guilds.append({
                "id": guild.id,
                "name": guild.name,
                "member_count": guild.member_count,
                "icon_url": str(guild.icon.url) if guild.icon else None,
                "in_voice": in_voice,
                "voice_channel": voice_channel_name
            })
        
        return guilds
    
    def get_guild_queue(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """
        Get queue information for a guild
        
        PHASE 1 TASK 1.1: IMPLEMENTED - Real Queue Integration
        
        This method now properly integrates with the Music cog's queue system
        instead of returning placeholder data.
        
        Args:
            guild_id: Guild ID
            
        Returns:
            Dictionary with queue information or None if not found
        """
        try:
            # Get guild
            guild = self.bot.get_guild(guild_id)
            if not guild:
                logger.warning(f"Guild {guild_id} not found")
                return None
            
            # Get Music cog - this is where the actual queue is stored
            music_cog = self.bot.get_cog('Music')
            if not music_cog:
                logger.warning("Music cog not loaded")
                return None
            
            # Get the actual queue from Music cog
            queue = music_cog.get_queue(guild_id)
            
            # Get voice client state
            voice_client = guild.voice_client
            is_playing = voice_client.is_playing() if voice_client else False
            is_paused = voice_client.is_paused() if voice_client else False
            
            # Build current song data from queue.current
            current_song = None
            if queue.current:
                current_song = {
                    'title': queue.current.title,
                    'is_local': queue.current.is_local,
                    'source': str(queue.current.source) if queue.current.is_local else None
                }
            
            # Build upcoming songs list from queue
            upcoming_songs = []
            for idx, song in enumerate(queue.get_upcoming(limit=50)):
                upcoming_songs.append({
                    'title': song.title,
                    'is_local': song.is_local,
                    'position': idx
                })
            
            # Return complete queue information
            return {
                'guild_id': guild_id,
                'guild_name': guild.name,
                'current': current_song,
                'queue': upcoming_songs,
                'queue_length': len(queue),
                'loop': queue.loop,
                'volume': int(queue.volume * 100),  # Convert to percentage
                'is_playing': is_playing,
                'is_paused': is_paused,
                'voice_channel': voice_client.channel.name if voice_client else None
            }
            
        except Exception as e:
            logger.error(f"Error getting queue for guild {guild_id}: {e}", exc_info=True)
            return None
    
    async def get_all_queues(self) -> List[Dict[str, Any]]:
        """
        Get queue information for all guilds
        
        Returns:
            List of queue information dictionaries
        """
        queues = []
        for guild in self.bot.guilds:
            queue_info = self.get_guild_queue(guild.id)
            if queue_info:
                queues.append(queue_info)
        return queues
    
    async def execute_command(self, guild_id: int, command: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a bot command from the dashboard
        
        PHASE 1 TASK 1.2: TO BE IMPLEMENTED
        
        Args:
            guild_id: Guild ID
            command: Command name (play, pause, skip, stop, volume, loop)
            args: Command arguments
            
        Returns:
            Result dictionary with success status and message
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return {"success": False, "error": "Guild not found"}
            
            music_cog = self.bot.get_cog('Music')
            if not music_cog:
                return {"success": False, "error": "Music system not available"}
            
            # Get voice client
            voice_client = guild.voice_client
            args = args or {}
            
            # Basic command execution (will be enhanced in Phase 1 Task 1.2)
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
                if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
                    voice_client.stop()
                    await self._broadcast_update('command_executed', {
                        "guild_id": guild_id,
                        "command": "skip"
                    })
                    return {"success": True, "message": "Song skipped"}
                return {"success": False, "error": "Nothing is playing"}
            
            elif command == 'stop':
                if voice_client:
                    # Get queue and clear it
                    queue = music_cog.get_queue(guild_id)
                    queue.clear()
                    
                    voice_client.stop()
                    await self._broadcast_update('command_executed', {
                        "guild_id": guild_id,
                        "command": "stop"
                    })
                    return {"success": True, "message": "Playback stopped and queue cleared"}
                return {"success": False, "error": "Bot not in voice channel"}
            
            elif command == 'volume':
                volume = args.get('volume')
                if volume is None:
                    return {"success": False, "error": "Volume parameter required"}
                
                try:
                    vol_int = int(volume)
                    if not 0 <= vol_int <= 100:
                        return {"success": False, "error": "Volume must be between 0 and 100"}
                    
                    # Update queue volume
                    queue = music_cog.get_queue(guild_id)
                    queue.volume = vol_int / 100
                    
                    # Apply to current playing source
                    if voice_client and voice_client.source and hasattr(voice_client.source, 'volume'):
                        voice_client.source.volume = vol_int / 100
                    
                    await self._broadcast_update('command_executed', {
                        "guild_id": guild_id,
                        "command": "volume",
                        "volume": vol_int
                    })
                    return {"success": True, "message": f"Volume set to {vol_int}%"}
                except ValueError:
                    return {"success": False, "error": "Invalid volume value"}
            
            elif command == 'loop':
                queue = music_cog.get_queue(guild_id)
                queue.loop = not queue.loop
                status = 'enabled' if queue.loop else 'disabled'
                
                await self._broadcast_update('command_executed', {
                    "guild_id": guild_id,
                    "command": "loop",
                    "enabled": queue.loop
                })
                return {"success": True, "message": f"Loop {status}"}
            
            else:
                return {"success": False, "error": f"Unknown command: {command}"}
        
        except Exception as e:
            logger.error(f"Error executing command {command}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def get_bot_status_dict(self) -> Optional[Dict[str, Any]]:
        """
        Get bot status as dictionary (synchronous version)
        
        Returns:
            Dictionary with bot status or None if bot not ready
        """
        if not self.bot.is_ready():
            return None
        
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        return {
            'connected': True,
            'status': 'online',
            'guilds': len(self.bot.guilds),
            'uptime': f"{hours}h {minutes}m",
            'latency': round(self.bot.latency * 1000, 2),
            'user': str(self.bot.user) if self.bot.user else None,
            'user_id': self.bot.user.id if self.bot.user else None
        }
    
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
