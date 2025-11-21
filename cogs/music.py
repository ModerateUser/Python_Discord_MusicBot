"""
Music playback commands cog
"""
import discord
from discord.ext import commands
import os
import asyncio
from typing import Dict, Optional
import logging

from models.song import Song, MusicQueue
from services.audio_service import audio_service
from utils.embeds import create_search_embed, create_nowplaying_embed
from core.config import config

logger = logging.getLogger('discord_bot')


class Music(commands.Cog):
    """Music playback commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues: Dict[int, MusicQueue] = {}
        self._play_locks: Dict[int, asyncio.Lock] = {}  # Prevent race conditions
        self._cleanup_task = bot.loop.create_task(self._cleanup_inactive_queues())
    
    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
    
    async def _cleanup_inactive_queues(self):
        """Periodically cleanup queues for guilds the bot is no longer in"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                guild_ids = {guild.id for guild in self.bot.guilds}
                inactive_guilds = [gid for gid in self.queues.keys() if gid not in guild_ids]
                
                for guild_id in inactive_guilds:
                    logger.info(f"Cleaning up queue for inactive guild {guild_id}")
                    del self.queues[guild_id]
                    if guild_id in self._play_locks:
                        del self._play_locks[guild_id]
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in queue cleanup: {e}", exc_info=True)
    
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
    
    @commands.command(name='join')
    async def join(self, ctx: commands.Context):
        """Join the voice channel"""
        if not ctx.author.voice:
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
    async def play(self, ctx: commands.Context, *, query: str):
        """Play audio from YouTube/local file"""
        # Ensure bot is in voice channel
        if not ctx.voice_client:
            if ctx.author.voice:
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
        
        # Check queue size limit
        if len(queue) >= config.get('max_queue_size', 100):
            await ctx.send(f'❌ Queue is full! Maximum size: {config.get("max_queue_size", 100)}')
            return
        
        # Check if it's a local file
        if os.path.exists(query):
            # SECURITY: Validate file path
            if not config.is_file_allowed(query):
                await ctx.send('❌ This file is not allowed. Check file extension or location.')
                logger.warning(f"Blocked file access attempt: {query} by {ctx.author}")
                return
            
            try:
                song = Song(query, os.path.basename(query), is_local=True)
                queue.add(song)
                
                if not ctx.voice_client.is_playing():
                    await self._play_next(ctx)
                else:
                    await ctx.send(f'➕ Added to queue: **{song.title}**')
            except Exception as e:
                logger.error(f"Error adding local file: {e}", exc_info=True)
                await ctx.send('❌ Error adding local file to queue')
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
                    
                    song = Song(player, player.title, is_local=False)
                    queue.add(song)
                    
                    if not ctx.voice_client.is_playing():
                        await self._play_next(ctx)
                    else:
                        await ctx.send(f'➕ Added to queue: **{song.title}**')
                        
                except Exception as e:
                    logger.error(f"Play error: {e}", exc_info=True)
                    await ctx.send('❌ Error: Could not play that track')
    
    async def _play_next(self, ctx: commands.Context):
        """Play the next song in queue (thread-safe)"""
        guild_id = ctx.guild.id
        lock = self.get_play_lock(guild_id)
        
        # Prevent race conditions when multiple songs finish simultaneously
        async with lock:
            queue = self.get_queue(guild_id)
            
            # Check if voice client still exists
            if not ctx.voice_client or not ctx.voice_client.is_connected():
                logger.info(f"Voice client disconnected for guild {guild_id}")
                return
            
            song = queue.next()
            
            if song:
                def after_playing(error):
                    if error:
                        logger.error(f'Playback error: {error}')
                    
                    # Schedule next song in a thread-safe way
                    future = asyncio.run_coroutine_threadsafe(
                        self._play_next(ctx), 
                        self.bot.loop
                    )
                    try:
                        future.result(timeout=10)
                    except Exception as e:
                        logger.error(f"Error scheduling next song: {e}", exc_info=True)
                
                try:
                    if song.is_local:
                        source = audio_service.create_local_source(song.source)
                    else:
                        # For loop mode, we need to re-fetch the URL
                        if queue.loop and hasattr(song.source, 'data'):
                            url = song.source.data.get('webpage_url') or song.source.data.get('url')
                            if url:
                                # Re-create source for loop (prevents stale stream issues)
                                song.source = await audio_service.create_ytdl_source(
                                    url, 
                                    loop=self.bot.loop, 
                                    stream=True
                                )
                        source = song.source
                    
                    # Apply volume if set
                    if hasattr(source, 'volume'):
                        volume = queue.volume
                        source.volume = volume
                    
                    ctx.voice_client.play(source, after=after_playing)
                    
                    try:
                        await ctx.send(f'🎵 Now playing: **{song.title}**')
                    except discord.HTTPException:
                        # Channel might be deleted, log but don't crash
                        logger.warning(f"Could not send now playing message in guild {guild_id}")
                        
                except Exception as e:
                    logger.error(f"Playback error for {song.title}: {e}", exc_info=True)
                    try:
                        await ctx.send(f'❌ Error playing: **{song.title}**')
                    except discord.HTTPException:
                        pass
                    # Try to play next song
                    await self._play_next(ctx)
                    
            elif not ctx.voice_client.is_playing():
                try:
                    await ctx.send('✅ Queue finished')
                except discord.HTTPException:
                    pass
    
    @commands.command(name='search', aliases=['find'])
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
        if not ctx.voice_client:
            await ctx.send('❌ Not connected to voice')
            return
            
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send('⏭️ Skipped')
        else:
            await ctx.send('❌ Nothing is playing')
    
    @commands.command(name='stop')
    async def stop(self, ctx: commands.Context):
        """Stop playing and clear the queue"""
        guild_id = ctx.guild.id
        
        if guild_id in self.queues:
            self.queues[guild_id].clear()
            
        if ctx.voice_client:
            ctx.voice_client.stop()
            
        await ctx.send('⏹️ Stopped and cleared queue')
    
    @commands.command(name='loop', aliases=['repeat'])
    async def loop(self, ctx: commands.Context):
        """Toggle loop mode for current song"""
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        queue.loop = not queue.loop
        status = 'enabled 🔁' if queue.loop else 'disabled ❌'
        await ctx.send(f'Loop {status}')
    
    @commands.command(name='volume', aliases=['vol', 'v'])
    async def volume(self, ctx: commands.Context, vol: int):
        """Change volume (0-100)"""
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
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        
        if queue.current:
            embed = create_nowplaying_embed(queue.current, queue.loop)
            await ctx.send(embed=embed)
        else:
            await ctx.send('❌ Nothing is playing')
