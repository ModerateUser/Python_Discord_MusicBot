"""
Playlist management commands cog
"""
import discord
from discord.ext import commands
import os

from models.song import Song
from services.playlist_service import playlist_service
from services.audio_service import audio_service
from core.config import config
from utils.embeds import create_playlist_list_embed, create_playlist_show_embed

class Playlist(commands.Cog):
    """Playlist management commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    def get_music_cog(self):
        """Get the Music cog to access queues"""
        return self.bot.get_cog('Music')
    
    @commands.command(name='playlist', aliases=['pl'])
    async def playlist_command(self, ctx, action: str = None, name: str = None, *, query: str = None):
        """Manage playlists"""
        
        if not action:
            await ctx.send("❌ Usage: `@bot playlist <create/add/play/list/show/delete> [name] [song]`")
            return
        
        action = action.lower()
        
        if action == 'create':
            await self._create_playlist(ctx, name)
        elif action == 'add':
            await self._add_to_playlist(ctx, name, query)
        elif action == 'play':
            await self._play_playlist(ctx, name)
        elif action == 'list':
            await self._list_playlists(ctx)
        elif action == 'show':
            await self._show_playlist(ctx, name)
        elif action == 'delete':
            await self._delete_playlist(ctx, name)
        else:
            await ctx.send("❌ Invalid action. Use: `create`, `add`, `play`, `list`, `show`, or `delete`")
    
    async def _create_playlist(self, ctx, name: str):
        """Create a new playlist"""
        if not name:
            await ctx.send("❌ Usage: `@bot playlist create <n>`")
            return
        
        if playlist_service.create(name):
            await ctx.send(f'✅ Created playlist: **{name}**')
        else:
            await ctx.send(f'❌ Playlist **{name}** already exists')
    
    async def _add_to_playlist(self, ctx, name: str, query: str):
        """Add a song to a playlist"""
        if not name or not query:
            await ctx.send("❌ Usage: `@bot playlist add <n> <song url/path>`")
            return
        
        if not playlist_service.exists(name):
            await ctx.send(f'❌ Playlist **{name}** does not exist')
            return
        
        if os.path.exists(query):
            song_data = {'type': 'local', 'path': query, 'title': os.path.basename(query)}
        else:
            song_data = {'type': 'url', 'path': query, 'title': query}
        
        playlist_service.add_song(name, song_data)
        await ctx.send(f'➕ Added to playlist **{name}**')
    
    async def _play_playlist(self, ctx, name: str):
        """Play a playlist"""
        if not name:
            await ctx.send("❌ Usage: `@bot playlist play <n>`")
            return
        
        playlist = playlist_service.get_playlist(name)
        if not playlist:
            await ctx.send(f'❌ Playlist **{name}** does not exist')
            return
        
        if not playlist:
            await ctx.send(f'❌ Playlist **{name}** is empty')
            return
        
        if not ctx.voice_client:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send('❌ Join a voice channel first!')
                return
        
        music_cog = self.get_music_cog()
        if not music_cog:
            await ctx.send('❌ Music system not available')
            return
        
        queue = music_cog.get_queue(ctx.guild.id)
        
        async with ctx.typing():
            count = 0
            for item in playlist:
                try:
                    if item['type'] == 'local':
                        song = Song(item['path'], item['title'], is_local=True)
                        queue.add(song)
                        count += 1
                    else:
                        player = await audio_service.create_ytdl_source(item['path'], loop=self.bot.loop, stream=True)
                        song = Song(player, player.title, is_local=False)
                        queue.add(song)
                        count += 1
                except Exception as e:
                    print(f"Error adding {item.get('title', 'unknown')}: {e}")
        
        await ctx.send(f'📚 Loaded **{count}** songs from playlist **{name}**')
        
        if not ctx.voice_client.is_playing():
            await music_cog._play_next(ctx)
    
    async def _list_playlists(self, ctx):
        """List all playlists"""
        playlists = playlist_service.list_playlists()
        
        if not playlists:
            await ctx.send('📭 No playlists available')
            return
        
        embed = create_playlist_list_embed(playlists)
        await ctx.send(embed=embed)
    
    async def _show_playlist(self, ctx, name: str):
        """Show songs in a playlist"""
        if not name:
            await ctx.send("❌ Usage: `@bot playlist show <n>`")
            return
        
        playlist = playlist_service.get_playlist(name)
        if not playlist:
            await ctx.send(f'❌ Playlist **{name}** does not exist')
            return
        
        if not playlist:
            await ctx.send(f'📭 Playlist **{name}** is empty')
            return
        
        embed = create_playlist_show_embed(name, playlist)
        await ctx.send(embed=embed)
    
    async def _delete_playlist(self, ctx, name: str):
        """Delete a playlist (owner only)"""
        if str(ctx.author.id) != str(config.get('owner_id')):
            await ctx.send('❌ Only the bot owner can delete playlists')
            return
        
        if not name:
            await ctx.send("❌ Usage: `@bot playlist delete <n>`")
            return
        
        if playlist_service.delete(name):
            await ctx.send(f'🗑️ Deleted playlist: **{name}**')
        else:
            await ctx.send(f'❌ Playlist **{name}** does not exist')