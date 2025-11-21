"""
Dashboard Bridge Service - FULLY IMPLEMENTED
Provides real-time communication between Discord bot and web dashboard
Uses asyncio for same-process integration with minimal overhead
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
    queue_length: int
    voice_channel: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

class DashboardBridge:
    """Bridge service between Discord bot and web dashboard"""
    
    def __init__(self, bot: commands.Bot):
        """Initialize dashboard bridge"""
        self.bot = bot
        self.start_time = datetime.now()
        self._subscribers: List[Callable] = []
        self._state_cache: Dict[str, Any] = {}
        self._update_task: Optional[asyncio.Task] = None
        self.websocket_manager = None
        logger.info("Dashboard Bridge initialized")
    
    def set_websocket_manager(self, manager):
        """Set the WebSocket manager for broadcasting updates"""
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
        """Subscribe to state updates"""
        self._subscribers.append(callback)
        logger.debug(f"New subscriber added. Total: {len(self._subscribers)}")
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from state updates"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            logger.debug(f"Subscriber removed. Total: {len(self._subscribers)}")
    
    async def _broadcast_update(self, update_type: str, data: Dict[str, Any]):
        """Broadcast update to all subscribers and WebSocket clients"""
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
        for callback in self._subscribers[:]:
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
                await asyncio.sleep(5)
                
                state = await self.get_bot_status()
                
                if state != self._state_cache.get('bot_status'):
                    self._state_cache['bot_status'] = state
                    await self._broadcast_update('status_update', state.to_dict())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic update: {e}", exc_info=True)
    
    def get_queue(self, guild_id: int):
        """
        Get queue from Music cog
        
        Args:
            guild_id: Guild ID
            
        Returns:
            MusicQueue instance or None
        """
        music_cog = self.bot.get_cog('Music')
        if not music_cog:
            return None
        return music_cog.get_queue(guild_id)
    
    async def get_bot_status(self) -> BotStatus:
        """Get current bot status"""
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        uptime_str = f"{hours}h {minutes}m"
        
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
        """Get queue information for a guild"""
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return None
        
        music_cog = self.bot.get_cog('Music')
        if not music_cog:
            return None
        
        voice_client = guild.voice_client
        if not voice_client:
            return None
        
        queue = music_cog.get_queue(guild_id)
        if not queue:
            return None
        
        current_song = None
        if queue.current:
            current_song = {
                "title": queue.current.title,
                "is_local": queue.current.is_local,
                "source": str(queue.current.source) if queue.current.is_local else None
            }
        
        upcoming_songs = []
        for song in queue.get_upcoming(limit=50):
            upcoming_songs.append({
                "title": song.title,
                "is_local": song.is_local,
                "position": queue.songs.index(song) + 1
            })
        
        voice_channel_name = None
        voice_client = guild.voice_client
        if voice_client and voice_client.channel:
            voice_channel_name = voice_client.channel.name
        
        return QueueInfo(
            guild_id=guild.id,
            guild_name=guild.name,
            current_song=current_song,
            queue=upcoming_songs,
            is_playing=voice_client and voice_client.is_playing(),
            is_paused=voice_client and voice_client.is_paused(),
            volume=int(queue.volume * 100),
            loop_mode=queue.loop,
            queue_length=len(queue.songs),
            voice_channel=voice_channel_name
        )
    
    async def get_all_queues(self) -> List[QueueInfo]:
        """Get queue info for all guilds"""
        queues = []
        for guild in self.bot.guilds:
            q = await self.get_guild_queue(guild.id)
            if q:
                queues.append(q)
        return queues
    
    async def execute_command(self, guild_id: int, command: str, **kwargs) -> Dict[str, Any]:
        """Execute command from dashboard"""
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return {"success": False, "error": "Guild not found"}
        
        music_cog = self.bot.get_cog('Music')
        if not music_cog:
            return {"success": False, "error": "Music cog not available"}
        
        voice_client = guild.voice_client
        if not voice_client:
            return {"success": False, "error": "Bot not in voice channel"}
        
        try:
            if command == 'pause':
                if voice_client and voice_client.is_playing():
                    voice_client.pause()
                    await self._broadcast_update('command_executed', {"guild_id": guild_id, "command": "pause"})
                    return {"success": True, "message": "Paused"}
                return {"success": False, "error": "Nothing is playing"}
            
            elif command == 'resume':
                if voice_client and voice_client.is_paused():
                    voice_client.resume()
                    await self._broadcast_update('command_executed', {"guild_id": guild_id, "command": "resume"})
                    return {"success": True, "message": "Resumed"}
                return {"success": False, "error": "Nothing is paused"}
            
            elif command == 'skip':
                if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
                    voice_client.stop()
                    await self._broadcast_update('command_executed', {"guild_id": guild_id, "command": "skip"})
                    return {"success": True, "message": "Skipped"}
                return {"success": False, "error": "Nothing is playing"}
            
            elif command == 'stop':
                if voice_client:
                    queue = self.get_queue(guild_id)
                    if queue:
                        queue.clear()
                    voice_client.stop()
                    await self._broadcast_update('command_executed', {"guild_id": guild_id, "command": "stop"})
                    return {"success": True, "message": "Stopped"}
                return {"success": False, "error": "Not in voice"}
            
            elif command == 'volume':
                vol = kwargs.get('volume')
                if vol is None:
                    return {"success": False, "error": "Volume parameter missing"}
                try:
                    vol_int = int(vol)
                    if not 0 <= vol_int <= 100:
                        return {"success": False, "error": "Volume must be 0-100"}
                    
                    queue = self.get_queue(guild_id)
                    if queue:
                        queue.volume = vol_int / 100
                    
                    if voice_client and hasattr(voice_client.source, 'volume'):
                        voice_client.source.volume = vol_int / 100
                    
                    await self._broadcast_update('command_executed', {"guild_id": guild_id, "command": "volume", "volume": vol_int})
                    return {"success": True, "message": f"Volume set to {vol_int}%"}
                except Exception:
                    return {"success": False, "error": "Invalid volume"}
            
            elif command == 'loop':
                queue = self.get_queue(guild_id)
                if queue:
                    queue.loop = not queue.loop
                    await self._broadcast_update('command_executed', {"guild_id": guild_id, "command": "loop", "enabled": queue.loop})
                    return {"success": True, "message": f"Loop {'enabled' if queue.loop else 'disabled'}"}
                return {"success": False, "error": "Queue not found"}
            
            else:
                return {"success": False, "error": "Unknown command"}
                
        except Exception as e:
            logger.error(f"Error executing command {command}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def get_service_health(self) -> Dict[str, bool]:
        """Check health of services"""
        health = {
            "bot": self.bot.is_ready(),
            "dashboard_bridge": True
        }
        return health
    
    def on_guild_join(self, guild):
        """Handle guild join"""
        asyncio.create_task(self._broadcast_update('guild_join', {
            "guild_id": guild.id,
            "guild_name": guild.name,
            "member_count": guild.member_count
        }))
    
    def on_guild_remove(self, guild):
        """Handle guild leave"""
        asyncio.create_task(self._broadcast_update('guild_remove', {
            "guild_id": guild.id,
            "guild_name": guild.name
        }))
    
    def on_voice_state_update(self, member, before, after):
        """Handle voice state change"""
        if member.id == self.bot.user.id:
            asyncio.create_task(self._broadcast_update('voice_state_update', {
                "guild_id": member.guild.id,
                "connected": after.channel is not None,
                "channel_name": after.channel.name if after.channel else None
            }))
    
    def on_track_start(self, guild_id, track_info):
        """Handle track start"""
        asyncio.create_task(self._broadcast_update('track_start', {
            "guild_id": guild_id,
            "track": track_info
        }))
    
    def on_track_end(self, guild_id):
        """Handle track end"""
        asyncio.create_task(self._broadcast_update('track_end', {
            "guild_id": guild_id
        }))
    
    def on_queue_update(self, guild_id):
        """Handle queue update"""
        asyncio.create_task(self._broadcast_update('queue_update', {
            "guild_id": guild_id
        }))

# Global instance
_bridge_instance: Optional[DashboardBridge] = None

def get_dashboard_bridge() -> Optional[DashboardBridge]:
    return _bridge_instance

def set_dashboard_bridge(bridge: DashboardBridge):
    global _bridge_instance
    _bridge_instance = bridge
    logger.info("Global dashboard bridge instance set")
