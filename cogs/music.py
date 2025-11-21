"""
Music playback commands cog - ENHANCED FIXED VERSION
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
    """Music playback commands with comprehensive error handling"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues: Dict[int, MusicQueue] = {}
        self._play_locks: Dict[int, asyncio.Lock] = {}
        self._queue_size_locks: Dict[int, asyncio.Lock] = {}  # FIX #5: Separate lock for queue size
        self._cleanup_error_count: int = 0
        self._cleanup_task = bot.loop.create_task(self._cleanup_inactive_queues())
        logger.info("Music cog initialized")
    
    def cog_unload(self):
        """
        Cleanup when cog is unloaded
        FIX #8: Properly cleanup all resources
        """
        logger.info("Unloading Music cog - cleaning up resources")
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Disconnect all voice clients
        for guild_id in list(self.queues.keys()):
            voice_client = self.bot.get_guild(guild_id)
            if voice_client and voice_client.voice_client:
                asyncio.create_task(voice_client.voice_client.disconnect())
        
        # Clear all queues
        for queue in self.queues.values():
            queue.clear()
        
        # Clear data structures
        self.queues.clear()
        self._play_locks.clear()
        self._queue_size_locks.clear()
        
        logger.info("Music cog unloaded successfully")
    
    async def _cleanup_inactive_queues(self):
        """
        Periodically cleanup queues for guilds the bot is no longer in
        FIX #5: Add circuit breaker for persistent errors
        """
        while True:
            try:
                await asyncio.sleep(CLEANUP_INTERVAL)
                
                guild_ids = {guild.id for guild in self.bot.guilds}
                inactive_guilds = [gid for gid in self.queues.keys() if gid not in guild_ids]
                
                for guild_id in inactive_guilds:
                    logger.info(f"Cleaning up queue for inactive guild {guild_id}")
                    
                    # Clear queue before deleting
                    if guild_id in self.queues:
                        self.queues[guild_id].clear()
                        del self.queues[guild_id]
                    
                    if guild_id in self._play_locks:
                        del self._play_locks[guild_id]
                    
                    if guild_id in self._queue_size_locks:
                        del self._queue_size_locks[guild_id]
                
                # Reset error count on successful cleanup
                self._cleanup_error_count = 0
                        
            except asyncio.CancelledError:
                logger.info("Cleanup task cancelled")
                break
            except Exception as e:
                self._cleanup_error_count += 1
                logger.error(f"Error in queue cleanup (attempt {self._cleanup_error_count}): {e}", exc_info=True)
                
                # Circuit breaker: stop if too many errors
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
        """
        FIX #5: Get or create queue size lock for guild
        Separate lock to prevent race conditions when checking queue size
        """
        if guild_id not in self._queue_size_locks:
            self._queue_size_locks[guild_id] = asyncio.Lock()
        return self._queue_size_locks[guild_id]
    
    @commands.command(name='join')
    async def join(self, ctx: commands.Context):
        """Join the voice channel"""
        # FIX BUG #5 (REVISED): Check if in guild and if author is a Member
        if not ctx.guild:
            await ctx.send('❌ This command can only be used in a server!')
            return
        
        # Ensure we have a Member object with voice state
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
        
        # Clear queue and cleanup
        if guild_id in self.queues:
            self.queues[guild_id].clear()
        
        try:
            await ctx.voice_client.disconnect()
            await ctx.send('👋 Disconnected from voice channel')
        except Exception as e:
            logger.error(f"Error disconnecting: {e}", exc_info=True)
            await ctx.send('❌ Error disconnecting from voice channel')
    
    @commands.command(name='play', aliases=['p'])
    @commands.cooldown(1, 2, commands.BucketType.user)  # Rate limiting
    async def play(self, ctx: commands.Context, *, query: str):
        """
        Play audio from YouTube/local file
        FIX #5: Enhanced race condition protection with atomic queue size check
        FIX #6: Security - check file permissions before existence
        FIX #13: Query length validation
        FIX BUG #2: Store should_play decision and use consistently
        FIX BUG #5 (REVISED): Proper Member check without guild_only decorator
        """
        # Validate query length
        if not query or len(query) > MAX_QUERY_LENGTH:
            await ctx.send(f'❌ Query must be between 1 and {MAX_QUERY_LENGTH} characters')
            return
        
        # FIX BUG #5 (REVISED): Check if in guild
        if not ctx.guild:
            await ctx.send('❌ This command can only be used in a server!')
            return
        
        # Ensure bot is in voice channel
        if not ctx.voice_client:
            # Check if author has voice attribute and is in a voice channel
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
        
        # FIX BUG #2: Variable to store the decision made inside the lock
        should_play = False
        
        # FIX #5: Use dedicated lock for atomic queue size check and add operation
        async with queue_size_lock:
            # Check queue size limit INSIDE the lock
            current_size = len(queue)
            if current_size >= config.max_queue_size:
                await ctx.send(f'❌ Queue is full! Maximum size: {config.max_queue_size}')
                return
            
            # FIX #6: Check file permissions BEFORE checking existence
            # This prevents information disclosure
            is_potential_file = not query.startswith('http') and ('/' in query or '\\' in query or ':' in query)
            
            if is_potential_file:
                # Check permissions first
                if not config.is_file_allowed(query):
                    await ctx.send('❌ This file is not allowed. Check file extension or location.')
                    logger.warning(f"Blocked file access attempt: {query} by {ctx.author}")
                    return
                
                # Now check if it exists
                if os.path.exists(query):
                    try:
                        song = Song(query, os.path.basename(query), is_local=True)
                        queue.add(song)
                        
                        # FIX BUG #2: Check if we should start playing - store the decision
                        should_play = not ctx.voice_client.is_playing()
                        
                    except Exception as e:
                        logger.error(f"Error adding local file: {e}", exc_info=True)
                        await ctx.send('❌ Error adding local file to queue')
                        return
                else:
                    await ctx.send('❌ File not found')
                    return
            else:
                # It's a URL or search query
                async with ctx.typing():
                    try:
                        if not query.startswith('http'):
                            query = f"ytsearch:{query}"
                        
                        player = await audio_service.create_ytdl_source(query, loop=self.bot.loop, stream=True)
                        
                        if not player:
                            await ctx.send('❌ Could not find that track')
                            return
                        
                        # Store the webpage URL for re-fetching if needed
                        song = Song(player, player.title, is_local=False)
                        queue.add(song)
                        
                        # FIX BUG #2: Check if we should start playing - store the decision
                        should_play = not ctx.voice_client.is_playing()
                        
                    except Exception as e:
                        logger.error(f"Play error: {e}", exc_info=True)
                        await ctx.send('❌ Error: Could not play that track')
                        return
        
        # FIX BUG #2: Use the stored decision (don't re-check is_playing)
        # This prevents race conditions where another command starts playback between checks
        if should_play:
            # Start playback
            await self._play_next(ctx)
        else:
            # Only send "added to queue" if we're NOT starting playback
            await ctx.send(f'➕ Added to queue: **{song.title}**')
    
    async def _play_next(self, ctx: commands.Context, retry_count: int = 0):
        """
        Play the next song in queue (thread-safe with retry logic)
        
        FIX #1: Volume persistence for all sources
        FIX #2: Memory leak - cleanup old sources
        FIX #3: Deadlock - proper lock management
        FIX #4: Context loss - store guild/channel IDs
        FIX #9: Async context handling in callbacks
        
        Args:
            ctx: Command context
            retry_count: Number of retries attempted (for URL expiration handling)
        """
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id
        
        # FIX #4: Store IDs instead of context to prevent stale references
        guild = self.bot.get_guild(guild_id)
        if not guild:
            logger.warning(f"Guild {guild_id} not found, cannot play next")
            return
        
        voice_client = guild.voice_client
        if not voice_client or not voice_client.is_connected():
            logger.info(f"Voice client disconnected for guild {guild_id}")
            return
        
        play_lock = self.get_play_lock(guild_id)
        
        # FIX #3: Acquire lock only for queue operations, not for playback
        async with play_lock:
            queue = self.get_queue(guild_id)
            song = queue.next()
            
            if not song:
                # Queue is empty
                try:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        await channel.send('✅ Queue finished')
                except discord.HTTPException:
                    pass
                return
        
        # FIX #3: Lock is released here, before setting up callback
        # This prevents deadlock when after_playing tries to call _play_next
        
        # FIX #9: Create callback that properly handles async context
        def after_playing(error):
            if error:
                logger.error(f'Playback error: {error}')
            
            # FIX #9: Check if bot loop is still running before scheduling
            if self.bot.loop.is_closed():
                logger.warning(f"Bot loop closed, cannot schedule next song for guild {guild_id}")
                return
            
            # Use stored IDs instead of ctx
            coro = self._play_next_by_ids(guild_id, channel_id)
            
            try:
                # FIX #9: Use asyncio.run_coroutine_threadsafe with proper error handling
                future = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                
                # Wait for completion with timeout
                future.result(timeout=PLAYBACK_TIMEOUT)
            except asyncio.TimeoutError:
                logger.error(f"Timeout scheduling next song for guild {guild_id}")
            except RuntimeError as e:
                # FIX #9: Handle case where event loop is closed
                logger.error(f"Runtime error scheduling next song: {e}")
            except Exception as e:
                logger.error(f"Error scheduling next song: {e}", exc_info=True)
        
        try:
            source = None
            old_source = None
            
            if song.is_local:
                # Create local source
                base_source = audio_service.create_local_source(song.source)
                if not base_source:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        await channel.send(f'❌ Error loading local file: **{song.title}**')
                    await self._play_next_by_ids(guild_id, channel_id)
                    return
                
                # FIX #1: Wrap local sources in PCMVolumeTransformer for volume control
                queue = self.get_queue(guild_id)
                source = discord.PCMVolumeTransformer(base_source, volume=queue.volume)
                
            else:
                # For streamed songs, check if we need to re-fetch the URL
                queue = self.get_queue(guild_id)
                
                if queue.loop and hasattr(song.source, 'data'):
                    # FIX #2: Store old source for cleanup
                    old_source = song.source
                    
                    # Re-fetch URL for loop mode to prevent expiration
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
                            
                            # FIX #2: Cleanup old source to prevent memory leak
                            if old_source and hasattr(old_source, 'cleanup'):
                                try:
                                    old_source.cleanup()
                                except Exception as e:
                                    logger.warning(f"Error cleaning up old source: {e}")
                        else:
                            logger.error(f"Failed to re-fetch URL for {song.title}")
                            if retry_count < 2:
                                # Retry once
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
                
                # FIX #1: Apply volume to source
                if source and hasattr(source, 'volume'):
                    source.volume = queue.volume
            
            # Start playback
            voice_client.play(source, after=after_playing)
            
            # Send now playing message
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
            # Try to play next song
            await self._play_next_by_ids(guild_id, channel_id)
            
        except Exception as e:
            logger.error(f"Playback error for {song.title}: {e}", exc_info=True)
            channel = self.bot.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(f'❌ Error playing: **{song.title}**')
                except discord.HTTPException:
                    pass
            # Try to play next song
            await self._play_next_by_ids(guild_id, channel_id)
    
    async def _play_next_by_ids(self, guild_id: int, channel_id: int):
        """
        Helper method to play next song using guild and channel IDs
        FIX #4: Prevents context loss issues
        """
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
        
        # Create a minimal context-like object
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
    @commands.cooldown(1, 3, commands.BucketType.user)  # Rate limiting
    async def search(self, ctx: commands.Context, *, query: str):
        """
        Search for a song on YouTube
        FIX #13: Consistent query validation
        """
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
        
        # Apply to current playing source
        if ctx.voice_client.source and hasattr(ctx.voice_client.source, 'volume'):
            ctx.voice_client.source.volume = vol / 100
            
        await ctx.send(f'🔊 Volume set to **{vol}%**')
    
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
