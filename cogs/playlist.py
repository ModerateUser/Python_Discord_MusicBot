"""
Playlist management commands cog
"""
import discord
from discord.ext import commands
import os
import re
import logging
from typing import Optional

from models.song import Song
from services.playlist_service import playlist_service
from services.audio_service import audio_service
from core.config import config
from utils.embeds import create_playlist_list_embed, create_playlist_show_embed

logger = logging.getLogger('discord_bot')


class Playlist(commands.Cog):
    """Playlist management commands"""
    
    # Regex for valid playlist names (alphanumeric, spaces, hyphens, underscores)
    VALID_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s_-]{1,50}$')
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    def get_music_cog(self):
        """Get the Music cog to access queues"""
        return self.bot.get_cog('Music')
    
    def validate_playlist_name(self, name: str) -> tuple[bool, Optional[str]]:
        """
        Validate playlist name for security
        Returns: (is_valid, error_message)
        """
        if not name:
            return False, "Playlist name cannot be empty"
        
        if len(name) > 50:
            return False, "Playlist name must be 50 characters or less"
        
        if not self.VALID_NAME_PATTERN.match(name):
            return False, "Playlist name can only contain letters, numbers, spaces, hyphens, and underscores"
        
        # Prevent path traversal attempts
        if '..' in name or '/' in name or '\\' in name:
            return False, "Invalid characters in playlist name"
        
        return True, None
    
    @commands.command(name='playlist', aliases=['pl'])
    async def playlist_command(self, ctx: commands.Context, action: str = None, name: str = None, *, query: str = None):
        """Manage playlists"""
        
        if not action:
            await ctx.send(
                "❌ Usage: `!playlist <create/add/play/list/show/delete> [name] [song]`\n"
                "Examples:\n"
                "  `!playlist create MyPlaylist`\n"
                "  `!playlist add MyPlaylist https://youtube.com/...`\n"
                "  `!playlist play MyPlaylist`"
            )
            return
        
        action = action.lower()
        
        try:
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
        except Exception as e:
            logger.error(f"Playlist command error: {e}", exc_info=True)
            await ctx.send("❌ An error occurred processing your playlist command")
    
    async def _create_playlist(self, ctx: commands.Context, name: str):
        """Create a new playlist"""
        if not name:
            await ctx.send("❌ Usage: `!playlist create <name>`")
            return
        
        # Validate name
        is_valid, error_msg = self.validate_playlist_name(name)
        if not is_valid:
            await ctx.send(f"❌ {error_msg}")
            return
        
        try:
            if playlist_service.create(name):
                await ctx.send(f'✅ Created playlist: **{name}**')
                logger.info(f"Playlist '{name}' created by {ctx.author} ({ctx.author.id})")
            else:
                await ctx.send(f'❌ Playlist **{name}** already exists')
        except Exception as e:
            logger.error(f"Error creating playlist: {e}", exc_info=True)
            await ctx.send("❌ Error creating playlist")
    
    async def _add_to_playlist(self, ctx: commands.Context, name: str, query: str):
        """Add a song to a playlist"""
        if not name or not query:
            await ctx.send("❌ Usage: `!playlist add <name> <song url/path>`")
            return
        
        # Validate name
        is_valid, error_msg = self.validate_playlist_name(name)
        if not is_valid:
            await ctx.send(f"❌ {error_msg}")
            return
        
        if not playlist_service.exists(name):
            await ctx.send(f'❌ Playlist **{name}** does not exist')
            return
        
        # Check playlist size limit
        current_playlist = playlist_service.get_playlist(name)
        max_size = config.max_playlist_size
        if current_playlist and len(current_playlist) >= max_size:
            await ctx.send(f'❌ Playlist is full! Maximum size: {max_size}')
            return
        
        try:
            if os.path.exists(query):
                # SECURITY: Validate file path
                if not config.is_file_allowed(query):
                    await ctx.send('❌ This file is not allowed. Check file extension or location.')
                    logger.warning(f"Blocked playlist file access: {query} by {ctx.author}")
                    return
                
                song_data = {
                    'type': 'local',
                    'path': query,
                    'title': os.path.basename(query)
                }
            else:
                # Validate URL length
                if len(query) > 500:
                    await ctx.send('❌ URL is too long (max 500 characters)')
                    return
                
                song_data = {
                    'type': 'url',
                    'path': query,
                    'title': query[:100]  # Truncate title for storage
                }
            
            playlist_service.add_song(name, song_data)
            await ctx.send(f'➕ Added to playlist **{name}**')
            logger.info(f"Song added to playlist '{name}' by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error adding to playlist: {e}", exc_info=True)
            await ctx.send("❌ Error adding song to playlist")
    
    async def _play_playlist(self, ctx: commands.Context, name: str):
        """Play a playlist"""
        if not name:
            await ctx.send("❌ Usage: `!playlist play <name>`")
            return
        
        # Validate name
        is_valid, error_msg = self.validate_playlist_name(name)
        if not is_valid:
            await ctx.send(f"❌ {error_msg}")
            return
        
        playlist = playlist_service.get_playlist(name)
        if not playlist:
            await ctx.send(f'❌ Playlist **{name}** does not exist')
            return
        
        if len(playlist) == 0:
            await ctx.send(f'❌ Playlist **{name}** is empty')
            return
        
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
        
        music_cog = self.get_music_cog()
        if not music_cog:
            await ctx.send('❌ Music system not available')
            return
        
        queue = music_cog.get_queue(ctx.guild.id)
        
        # Check if adding playlist would exceed queue limit
        max_queue_size = config.max_queue_size
        if len(queue) + len(playlist) > max_queue_size:
            await ctx.send(
                f'❌ Adding this playlist would exceed queue limit!\n'
                f'Current queue: {len(queue)}, Playlist: {len(playlist)}, Max: {max_queue_size}'
            )
            return
        
        async with ctx.typing():
            count = 0
            failed = 0
            
            for item in playlist:
                try:
                    if item['type'] == 'local':
                        # Validate file still exists and is allowed
                        if not os.path.exists(item['path']):
                            logger.warning(f"Playlist file not found: {item['path']}")
                            failed += 1
                            continue
                        
                        if not config.is_file_allowed(item['path']):
                            logger.warning(f"Playlist file not allowed: {item['path']}")
                            failed += 1
                            continue
                        
                        song = Song(item['path'], item['title'], is_local=True)
                        queue.add(song)
                        count += 1
                    else:
                        player = await audio_service.create_ytdl_source(
                            item['path'], 
                            loop=self.bot.loop, 
                            stream=True
                        )
                        
                        if player:
                            song = Song(player, player.title, is_local=False)
                            queue.add(song)
                            count += 1
                        else:
                            failed += 1
                            
                except Exception as e:
                    logger.error(f"Error adding playlist item {item.get('title', 'unknown')}: {e}")
                    failed += 1
        
        result_msg = f'📚 Loaded **{count}** songs from playlist **{name}**'
        if failed > 0:
            result_msg += f'\n⚠️ {failed} songs failed to load'
        
        await ctx.send(result_msg)
        
        if count > 0 and not ctx.voice_client.is_playing():
            await music_cog._play_next(ctx)
    
    async def _list_playlists(self, ctx: commands.Context):
        """List all playlists"""
        try:
            playlists = playlist_service.list_playlists()
            
            if not playlists:
                await ctx.send('📭 No playlists available')
                return
            
            embed = create_playlist_list_embed(playlists)
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error listing playlists: {e}", exc_info=True)
            await ctx.send("❌ Error listing playlists")
    
    async def _show_playlist(self, ctx: commands.Context, name: str):
        """Show songs in a playlist"""
        if not name:
            await ctx.send("❌ Usage: `!playlist show <name>`")
            return
        
        # Validate name
        is_valid, error_msg = self.validate_playlist_name(name)
        if not is_valid:
            await ctx.send(f"❌ {error_msg}")
            return
        
        try:
            playlist = playlist_service.get_playlist(name)
            if not playlist:
                await ctx.send(f'❌ Playlist **{name}** does not exist')
                return
            
            if len(playlist) == 0:
                await ctx.send(f'📭 Playlist **{name}** is empty')
                return
            
            embed = create_playlist_show_embed(name, playlist)
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error showing playlist: {e}", exc_info=True)
            await ctx.send("❌ Error displaying playlist")
    
    async def _delete_playlist(self, ctx: commands.Context, name: str):
        """Delete a playlist (owner only)"""
        # Use type-safe owner check
        if not config.is_owner(ctx.author.id):
            await ctx.send('❌ Only the bot owner can delete playlists')
            logger.warning(f"Unauthorized playlist delete attempt by {ctx.author} ({ctx.author.id})")
            return
        
        if not name:
            await ctx.send("❌ Usage: `!playlist delete <name>`")
            return
        
        # Validate name
        is_valid, error_msg = self.validate_playlist_name(name)
        if not is_valid:
            await ctx.send(f"❌ {error_msg}")
            return
        
        try:
            if playlist_service.delete(name):
                await ctx.send(f'🗑️ Deleted playlist: **{name}**')
                logger.info(f"Playlist '{name}' deleted by {ctx.author} ({ctx.author.id})")
            else:
                await ctx.send(f'❌ Playlist **{name}** does not exist')
        except Exception as e:
            logger.error(f"Error deleting playlist: {e}", exc_info=True)
            await ctx.send("❌ Error deleting playlist")


async def setup(bot: commands.Bot):
    """Setup function for cog loading"""
    await bot.add_cog(Playlist(bot))
