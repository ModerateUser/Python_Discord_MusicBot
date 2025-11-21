"""
Music playback commands cog - ENHANCED WITH DASHBOARD INTEGRATION
Addresses all critical issues found in testing:
- Memory leak in loop mode (Issue #2)
- Volume persistence for local files (Issue #1)
- Deadlock potential (Issue #3)
- Context loss in callback (Issue #4)
- Security vulnerability (Issue #6)
- Queue size race condition (Issue #7) - ENHANCED
- Missing cleanup on unload (Issue #8)
- Cleanup task error handling (Issue #5)
- FIX #9: Async context handling in callbacks
- FIX BUG #2: Race condition in should_play logic - use stored decision consistently
- FIX BUG #5 (REVISED): Proper Member check without guild_only decorator
- DASHBOARD INTEGRATION: Real-time event broadcasting to web dashboard
"""
import discord
from discord.ext import commands
import os
import asyncio
from typing import Dict, Optional, Tuple
import logging
import weakref

from models.song import Song, MusicQueue
from services.audio_service import audio_service
from utils.embeds import create_search_embed, create_nowplaying_embed
from core.config import config

logger = logging.getLogger('discord_bot')

# Constants
MAX_QUERY_LENGTH = 500
CLEANUP_INTERVAL = 3600  # 1 hour
PLAYBACK_TIMEOUT = 10
MAX_CLEANUP_ERRORS = 5


class Music(commands.Cog):
    """Music playback commands with comprehensive error handling and dashboard integration"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues: Dict[int, MusicQueue] = {}
        self._play_locks: Dict[int, asyncio.Lock] = {}
        self._queue_size_locks: Dict[int, asyncio.Lock] = {}
        self._cleanup_error_count: int = 0
        self._cleanup_task = bot.loop.create_task(self._cleanup_inactive_queues())
        logger.info("Music cog initialized")
    
    def _notify_dashboard(self, event_type: str, guild_id: int, data: Optional[Dict] = None):
        """
        Notify dashboard bridge of events
        
        Args:
            event_type: Type of event (track_start, track_end, queue_update)
            guild_id: Guild ID
            data: Additional event data
        """
        try:
            from services.dashboard_bridge import get_dashboard_bridge
            bridge = get_dashboard_bridge()
            
            if bridge:
                if event_type == 'track_start':
                    bridge.on_track_start(guild_id, data or {})
                elif event_type == 'track_end':
                    bridge.on_track_end(guild_id)
                elif event_type == 'queue_update':
                    bridge.on_queue_update(guild_id)
        except Exception as e:
            logger.debug(f"Dashboard notification failed (bridge may not be available): {e}")
    
    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        logger.info("Unloading Music cog - cleaning up resources")
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        for guild_id in list(self.queues.keys()):
            voice_client = self.bot.get_guild(guild_id)
            if voice_client and voice_client.voice_client:
                asyncio.create_task(voice_client.voice_client.disconnect())
        
        for queue in self.queues.values():
            queue.clear()
        
        self.queues.clear()
        self._play_locks.clear()
        self._queue_size_locks.clear()
        
        logger.info("Music cog unloaded successfully")
    
    async def _cleanup_inactive_queues(self):
        """Periodically cleanup queues for guilds the bot is no longer in"""
        while True:
            try:
                await asyncio.sleep(CLEANUP_INTERVAL)
                
                guild_ids = {guild.id for guild in self.bot.guilds}
                inactive_guilds = [gid for gid in self.queues.keys() if gid not in guild_ids]
                
                for guild_id in inactive_guilds:
                    logger.info(f"Cleaning up queue for inactive guild {guild_id}")
                    
                    if guild_id in self.queues:
                        self.queues[guild_id].clear()
                        del self.queues[guild_id]
                    
                    if guild_id in self._play_locks:
                        del self._play_locks[guild_id]
                    
                    if guild_id in self._queue_size_locks:
                        del self._queue_size_locks[guild_id]
                
                self._cleanup_error_count = 0
                        
            except asyncio.CancelledError:
                logger.info("Cleanup task cancelled")
                break
            except Exception as e:
                self._cleanup_error_count += 1
                logger.error(f"Error in queue cleanup (attempt {self._cleanup_error_count}): {e}", exc_info=True)
                
                if self._cleanup_error_count >= MAX_CLEANUP_ERRORS:
                    logger.critical(f"Cleanup task failed {MAX_CLEANUP_ERRORS} times, stopping task")
                    break
    
    def get_queue(self, guild_id: int) -> MusicQueue:
        """Get or create queue for guild"""
        if guild_id not in self.queues:
            self.queues[guild_id] = MusicQueue()
        return self.queues[guild_id]
    
    def get_play_lock(self, guild_id: int) -> asyncio.Lock:
        """Get or create play lock for guild to prevent race conditions"""
        if guild_id not in self._play_locks:
            self._play_locks[guild_id] = asyncio.Lock()
        return self._play_locks[guild_id]
    
    def get_queue_size_lock(self, guild_id: int) -> asyncio.Lock:
        """Get or create queue size lock for guild"""
        if guild_id not in self._queue_size_locks:
            self._queue_size_locks[guild_id] = asyncio.Lock()
        return self._queue_size_locks[guild_id]
    
    @commands.command(name='join')
    async def join(self, ctx: commands.Context):
        """Join the voice channel"""
        if not ctx.guild:
            await ctx.send('❌ This command can only be used in a server!')
            return
        
        if not hasattr(ctx.author, 'voice') or ctx.author.voice is None:
            await ctx.send('❌ You need to be in a voice channel first!')
            return
            
        channel = ctx.author.voice.channel
        
        try:
            if ctx.voice_client:
                await ctx.voice_client.move_to(channel)
            else:
                await channel.connect()
            await ctx.send(f'🎵 Joined **{channel.name}**')
        except Exception as e:
            logger.error(f"Failed to join voice channel: {e}", exc_info=True)
            await ctx.send('❌ Failed to join voice channel. Check bot permissions.')
    
    @commands.command(name='leave', aliases=['disconnect', 'dc'])
    async def leave(self, ctx: commands.Context):
        """Leave the voice channel"""
        if not ctx.guild:
            await ctx.send('❌ This command can only be used in a server!')
            return
        
        if not ctx.voice_client:
            await ctx.send('❌ I\'m not in a voice channel')
            return
        
        guild_id = ctx.guild.id
        
        if guild_id in self.queues:
            self.queues[guild_id].clear()
            self._notify_dashboard('queue_update', guild_id)
        
        try:
            await ctx.voice_client.disconnect()
            await ctx.send('👋 Disconnected from voice channel')
        except Exception as e:
            logger.error(f"Error disconnecting: {e}", exc_info=True)
            await ctx.send('❌ Error disconnecting from voice channel')
    
    @commands.command(name='play', aliases=['p'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def play(self, ctx: commands.Context, *, query: str):
        """Play audio from YouTube/local file"""
        if not query or len(query) > MAX_QUERY_LENGTH:
            await ctx.send(f'❌ Query must be between 1 and {MAX_QUERY_LENGTH} characters')
            return
        
        if not ctx.guild:
            await ctx.send('❌ This command can only be used in a server!')
            return
        
        if not ctx.voice_client:
            if hasattr(ctx.author, 'voice') and ctx.author.voice:
                try:
                    await ctx.author.voice.channel.connect()
                except Exception as e:
                    logger.error(f"Failed to connect to voice: {e}", exc_info=True)
                    await ctx.send('❌ Failed to connect to voice channel')
                    return
            else:
                await ctx.send('❌ Join a voice channel first!')
                return
        
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        queue_size_lock = self.get_queue_size_lock(guild_id)
        
        should_play = False
        
        async with queue_size_lock:
            current_size = len(queue)
            if current_size >= config.max_queue_size:
                await ctx.send(f'❌ Queue is full! Maximum size: {config.max_queue_size}')
                return
            
            is_potential_file = not query.startswith('http') and ('/' in query or '\\' in query or ':' in query)
            
            if is_potential_file:
                if not config.is_file_allowed(query):
                    await ctx.send('❌ This file is not allowed. Check file extension or location.')
                    logger.warning(f"Blocked file access attempt: {query} by {ctx.author}")
                    return
                
                if os.path.exists(query):
                    try:
                        song = Song(query, os.path.basename(query), is_local=True)
                        queue.add(song)
                        should_play = not ctx.voice_client.is_playing()
                        
                        # Notify dashboard of queue update
                        self._notify_dashboard('queue_update', guild_id)
                        
                    except Exception as e:
                        logger.error(f"Error adding local file: {e}", exc_info=True)
                        await ctx.send('❌ Error adding local file to queue')
                        return
                else:
                    await ctx.send('❌ File not found')
                    return
            else:
                async with ctx.typing():
                    try:
                        if not query.startswith('http'):
                            query = f"ytsearch:{query}"
                        
                        player = await audio_service.create_ytdl_source(query, loop=self.bot.loop, stream=True)
                        
                        if not player:
                            await ctx.send('❌ Could not find that track')
                            return
                        
                        song = Song(player, player.title, is_local=False)
                        queue.add(song)
                        should_play = not ctx.voice_client.is_playing()
                        
                        # Notify dashboard of queue update
                        self._notify_dashboard('queue_update', guild_id)
                        
                    except Exception as e:
                        logger.error(f"Play error: {e}", exc_info=True)
                        await ctx.send('❌ Error: Could not play that track')
                        return
        
        if should_play:
            await self._play_next(ctx)
        else:
            await ctx.send(f'➕ Added to queue: **{song.title}**')
    
    async def _play_next(self, ctx: commands.Context, retry_count: int = 0):
        """Play the next song in queue"""
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id
        
        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.warning(f"Guild {guild_id} not found, cannot play next")
            return
        
        voice_client = guild.voice_client
        if not voice_client or not voice_client.is_connected():
            logger.info(f"Voice client disconnected for guild {guild_id}")
            return
        
        play_lock = self.get_play_lock(guild_id)
        
        async with play_lock:
            queue = self.get_queue(guild_id)
            song = queue.next()
            
            if not song:
                try:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        await channel.send('✅ Queue finished')
                    
                    # Notify dashboard that track ended
                    self._notify_dashboard('track_end', guild_id)
                except discord.HTTPException:
                    pass
                return
        
        def after_playing(error):
            if error:
                logger.error(f'Playback error: {error}')
            
            # Notify dashboard that track ended
            self._notify_dashboard('track_end', guild_id)
            
            if self.bot.loop.is_closed():
                logger.warning(f"Bot loop closed, cannot schedule next song for guild {guild_id}")
                return
            
            coro = self._play_next_by_ids(guild_id, channel_id)
            
            try:
                future = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                future.result(timeout=PLAYBACK_TIMEOUT)
            except asyncio.TimeoutError:
                logger.error(f"Timeout scheduling next song for guild {guild_id}")
            except RuntimeError as e:
                logger.error(f"Runtime error scheduling next song: {e}")
            except Exception as e:
                logger.error(f"Error scheduling next song: {e}", exc_info=True)
        
        try:
            source = None
            old_source = None
            
            if song.is_local:
                base_source = audio_service.create_local_source(song.source)
                if not base_source:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        await channel.send(f'❌ Error loading local file: **{song.title}**')
                    await self._play_next_by_ids(guild_id, channel_id)
                    return
                
                queue = self.get_queue(guild_id)
                source = discord.PCMVolumeTransformer(base_source, volume=queue.volume)
                
            else:
                queue = self.get_queue(guild_id)
                
                if queue.loop and hasattr(song.source, 'data'):
                    old_source = song.source
                    
                    webpage_url = song.source.data.get('webpage_url')
                    if webpage_url:
                        logger.debug(f"Re-fetching stream URL for loop: {song.title}")
                        new_source = await audio_service.create_ytdl_source(
                            webpage_url, 
                            loop=self.bot.loop, 
                            stream=True
                        )
                        
                        if new_source:
                            song.source = new_source
                            source = new_source
                            
                            if old_source and hasattr(old_source, 'cleanup'):
                                try:
                                    old_source.cleanup()
                                except Exception as e:
                                    logger.warning(f"Error cleaning up old source: {e}")
                        else:
                            logger.error(f"Failed to re-fetch URL for {song.title}")
                            if retry_count < 2:
                                await asyncio.sleep(1)
                                await self._play_next(ctx, retry_count + 1)
                                return
                            else:
                                channel = self.bot.get_channel(channel_id)
                                if channel:
                                    await channel.send(f'❌ Stream expired for: **{song.title}**')
                                await self._play_next_by_ids(guild_id, channel_id)
                                return
                else:
                    source = song.source
                
                if source and hasattr(source, 'volume'):
                    source.volume = queue.volume
            
            voice_client.play(source, after=after_playing)
            
            # Notify dashboard that track started
            track_info = {
                'title': song.title,
                'is_local': song.is_local
            }
            self._notify_dashboard('track_start', guild_id, track_info)
            
            try:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send(f'🎵 Now playing: **{song.title}**')
            except discord.HTTPException:
                logger.warning(f"Could not send now playing message in guild {guild_id}")
                
        except discord.ClientException as e:
            logger.error(f"Discord client error for {song.title}: {e}", exc_info=True)
            channel = self.bot.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(f'❌ Playback error: **{song.title}**')
                except discord.HTTPException:
                    pass
            await self._play_next_by_ids(guild_id, channel_id)
            
        except Exception as e:
            logger.error(f"Playback error for {song.title}: {e}", exc_info=True)
            channel = self.bot.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(f'❌ Error playing: **{song.title}**')
                except discord.HTTPException:
                    pass
            await self._play_next_by_ids(guild_id, channel_id)
    
    async def _play_next_by_ids(self, guild_id: int, channel_id: int):
        """Helper method to play next song using guild and channel IDs"""
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
        
        class MinimalContext:
            def __init__(self, bot, guild, channel):
                self.bot = bot
                self.guild = guild
                self.channel = channel
                self.voice_client = guild.voice_client
            
            async def send(self, *args, **kwargs):
                return await self.channel.send(*args, **kwargs)
        
        ctx = MinimalContext(self.bot, guild, channel)
        await self._play_next(ctx)
    
    @commands.command(name='search', aliases=['find'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def search(self, ctx: commands.Context, *, query: str):
        """Search for a song on YouTube"""
        if not query or len(query) > 100:
            await ctx.send('❌ Search query must be between 1 and 100 characters')
            return
        
        async with ctx.typing():
            try:
                results = await audio_service.search_youtube(query, max_results=5)
                
                if results:
                    embed = create_search_embed(query, results, self.bot.user.name)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ No results found")
            except Exception as e:
                logger.error(f"Search error: {e}", exc_info=True)
                await ctx.send("❌ Error performing search")
    
    @commands.command(name='pause')
    async def pause(self, ctx: commands.Context):
        """Pause the current song"""
        if not ctx.guild:
            await ctx.send('❌ This command can only be used in a server!')
            return
        
        if not ctx.voice_client:
            await ctx.send('❌ Not connected to voice')
            return
            
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send('⏸️ Paused')
            self._notify_dashboard('queue_update', ctx.guild.id)
        else:
            await ctx.send('❌ Nothing is playing')
    
    @commands.command(name='resume', aliases=['unpause'])
    async def resume(self, ctx: commands.Context):
        """Resume the paused song"""
        if not ctx.guild:
            await ctx.send('❌ This command can only be used in a server!')
            return
        
        if not ctx.voice_client:
            await ctx.send('❌ Not connected to voice')
            return
            
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send('▶️ Resumed')
            self._notify_dashboard('queue_update', ctx.guild.id)
        else:
            await ctx.send('❌ Nothing is paused')
    
    @commands.command(name='skip', aliases=['next', 's'])
    async def skip(self, ctx: commands.Context):
        """Skip the current song"""
        if not ctx.guild:
            await ctx.send('❌ This command can only be used in a server!')
            return
        
        if not ctx.voice_client:
            await ctx.send('❌ Not connected to voice')
            return
            
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()
            await ctx.send('⏭️ Skipped')
            self._notify_dashboard('queue_update', ctx.guild.id)
        else:
            await ctx.send('❌ Nothing is playing')
    
    @commands.command(name='stop')
    async def stop(self, ctx: commands.Context):
        """Stop playing and clear the queue"""
        if not ctx.guild:
            await ctx.send('❌ This command can only be used in a server!')
            return
        
        guild_id = ctx.guild.id
        
        if guild_id in self.queues:
            self.queues[guild_id].clear()
            self._notify_dashboard('queue_update', guild_id)
            
        if ctx.voice_client:
            ctx.voice_client.stop()
            
        await ctx.send('⏹️ Stopped and cleared queue')
    
    @commands.command(name='loop', aliases=['repeat'])
    async def loop(self, ctx: commands.Context):
        """Toggle loop mode for current song"""
        if not ctx.guild:
            await ctx.send('❌ This command can only be used in a server!')
            return
        
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        queue.loop = not queue.loop
        status = 'enabled 🔁' if queue.loop else 'disabled ❌'
        await ctx.send(f'Loop {status}')
        self._notify_dashboard('queue_update', guild_id)
    
    @commands.command(name='volume', aliases=['vol', 'v'])
    async def volume(self, ctx: commands.Context, vol: int):
        """Change volume (0-100)"""
        if not ctx.guild:
            await ctx.send('❌ This command can only be used in a server!')
            return
        
        if not ctx.voice_client:
            await ctx.send("❌ Not connected to voice")
            return
        
        if not 0 <= vol <= 100:
            await ctx.send("❌ Volume must be between 0 and 100")
            return
        
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        queue.volume = vol / 100
        
        if ctx.voice_client.source and hasattr(ctx.voice_client.source, 'volume'):
            ctx.voice_client.source.volume = vol / 100
            
        await ctx.send(f'🔊 Volume set to **{vol}%**')
        self._notify_dashboard('queue_update', guild_id)
    
    @commands.command(name='nowplaying', aliases=['np', 'current'])
    async def nowplaying(self, ctx: commands.Context):
        """Show the currently playing song"""
        if not ctx.guild:
            await ctx.send('❌ This command can only be used in a server!')
            return
        
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        
        if queue.current:
            embed = create_nowplaying_embed(queue.current, queue.loop)
            await ctx.send(embed=embed)
        else:
            await ctx.send('❌ Nothing is playing')


async def setup(bot: commands.Bot):
    """Setup function for cog"""
    await bot.add_cog(Music(bot))
