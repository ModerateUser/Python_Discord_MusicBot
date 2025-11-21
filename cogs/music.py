"""
Music playback commands cog
"""
import discord
from discord.ext import commands
import os
import asyncio
from typing import Dict

from models.song import Song, MusicQueue
from services.audio_service import audio_service
from utils.embeds import create_search_embed, create_nowplaying_embed

class Music(commands.Cog):
    """Music playback commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues: Dict[int, MusicQueue] = {}
    
    def get_queue(self, guild_id: int) -> MusicQueue:
        """Get or create queue for guild"""
        if guild_id not in self.queues:
            self.queues[guild_id] = MusicQueue()
        return self.queues[guild_id]
    
    @commands.command(name='join')
    async def join(self, ctx):
        """Join the voice channel"""
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if ctx.voice_client:
                await ctx.voice_client.move_to(channel)
            else:
                await channel.connect()
            await ctx.send(f'🎵 Joined **{channel.name}**')
        else:
            await ctx.send('❌ You need to be in a voice channel first!')
    
    @commands.command(name='leave', aliases=['disconnect', 'dc'])
    async def leave(self, ctx):
        """Leave the voice channel"""
        if ctx.voice_client:
            guild_id = ctx.guild.id
            if guild_id in self.queues:
                self.queues[guild_id].clear()
            await ctx.voice_client.disconnect()
            await ctx.send('👋 Disconnected from voice channel')
        else:
            await ctx.send('❌ I\'m not in a voice channel')
    
    @commands.command(name='play', aliases=['p'])
    async def play(self, ctx, *, query: str):
        """Play audio from YouTube/local file"""
        if not ctx.voice_client:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send('❌ Join a voice channel first!')
                return
        
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        
        # Check if it's a local file
        if os.path.exists(query):
            song = Song(query, os.path.basename(query), is_local=True)
            queue.add(song)
            
            if not ctx.voice_client.is_playing():
                await self._play_next(ctx)
            else:
                await ctx.send(f'➕ Added to queue: **{song.title}**')
        else:
            # It's a URL or search query
            async with ctx.typing():
                try:
                    if not query.startswith('http'):
                        query = f"ytsearch:{query}"
                    
                    player = await audio_service.create_ytdl_source(query, loop=self.bot.loop, stream=True)
                    song = Song(player, player.title, is_local=False)
                    queue.add(song)
                    
                    if not ctx.voice_client.is_playing():
                        await self._play_next(ctx)
                    else:
                        await ctx.send(f'➕ Added to queue: **{song.title}**')
                except Exception as e:
                    await ctx.send(f'❌ Error: Could not play that track')
                    print(f"Play error: {e}")
    
    async def _play_next(self, ctx):
        """Play the next song in queue"""
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        
        song = queue.next()
        
        if song:
            def after_playing(error):
                if error:
                    print(f'Error: {error}')
                asyncio.run_coroutine_threadsafe(self._play_next(ctx), self.bot.loop)
            
            try:
                if song.is_local:
                    source = audio_service.create_local_source(song.source)
                else:
                    if queue.loop:
                        url = song.source.data.get('webpage_url') or song.source.data.get('url')
                        song.source = await audio_service.create_ytdl_source(url, loop=self.bot.loop, stream=True)
                    source = song.source
                
                ctx.voice_client.play(source, after=after_playing)
                await ctx.send(f'🎵 Now playing: **{song.title}**')
            except Exception as e:
                await ctx.send(f'❌ Error playing: **{song.title}**')
                print(f"Playback error: {e}")
                await self._play_next(ctx)
        elif ctx.voice_client and not ctx.voice_client.is_playing():
            await ctx.send('✅ Queue finished')
    
    @commands.command(name='search', aliases=['find'])
    async def search(self, ctx, *, query: str):
        """Search for a song on YouTube"""
        async with ctx.typing():
            results = await audio_service.search_youtube(query, max_results=5)
            
            if results:
                embed = create_search_embed(query, results, self.bot.user.name)
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ No results found")
    
    @commands.command(name='pause')
    async def pause(self, ctx):
        """Pause the current song"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send('⏸️ Paused')
        else:
            await ctx.send('❌ Nothing is playing')
    
    @commands.command(name='resume', aliases=['unpause'])
    async def resume(self, ctx):
        """Resume the paused song"""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send('▶️ Resumed')
        else:
            await ctx.send('❌ Nothing is paused')
    
    @commands.command(name='skip', aliases=['next', 's'])
    async def skip(self, ctx):
        """Skip the current song"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send('⏭️ Skipped')
        else:
            await ctx.send('❌ Nothing is playing')
    
    @commands.command(name='stop')
    async def stop(self, ctx):
        """Stop playing and clear the queue"""
        guild_id = ctx.guild.id
        if guild_id in self.queues:
            self.queues[guild_id].clear()
        if ctx.voice_client:
            ctx.voice_client.stop()
        await ctx.send('⏹️ Stopped and cleared queue')
    
    @commands.command(name='loop', aliases=['repeat'])
    async def loop(self, ctx):
        """Toggle loop mode for current song"""
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        queue.loop = not queue.loop
        status = 'enabled 🔁' if queue.loop else 'disabled ❌'
        await ctx.send(f'Loop {status}')
    
    @commands.command(name='volume', aliases=['vol', 'v'])
    async def volume(self, ctx, vol: int):
        """Change volume (0-100)"""
        if not ctx.voice_client:
            await ctx.send("❌ Not connected to voice")
            return
        
        if not 0 <= vol <= 100:
            await ctx.send("❌ Volume must be between 0 and 100")
            return
        
        if ctx.voice_client.source:
            ctx.voice_client.source.volume = vol / 100
            await ctx.send(f'🔊 Volume set to **{vol}%**')
        else:
            await ctx.send("❌ Nothing is playing")
    
    @commands.command(name='nowplaying', aliases=['np', 'current'])
    async def nowplaying(self, ctx):
        """Show the currently playing song"""
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        
        if queue.current:
            embed = create_nowplaying_embed(queue.current, queue.loop)
            await ctx.send(embed=embed)
        else:
            await ctx.send('❌ Nothing is playing')