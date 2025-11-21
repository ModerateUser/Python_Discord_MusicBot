"""
Discord embed creation utilities
"""
import discord
from typing import List, Dict
from models.song import Song, MusicQueue

def create_search_embed(query: str, results: list, bot_name: str) -> discord.Embed:
    """Create search results embed"""
    embed = discord.Embed(
        title=f"🔍 Search Results for: {query}",
        color=discord.Color.blue()
    )
    
    for i, result in enumerate(results, 1):
        duration = result.get('duration', 0)
        mins, secs = divmod(duration, 60)
        embed.add_field(
            name=f"{i}. {result['title'][:60]}",
            value=f"Duration: {mins}:{secs:02d}",
            inline=False
        )
    
    embed.set_footer(text=f"Use @{bot_name} play <song name> to play")
    return embed

def create_queue_embed(queue: MusicQueue) -> discord.Embed:
    """Create queue display embed"""
    embed = discord.Embed(
        title="🎵 Music Queue",
        color=discord.Color.purple()
    )
    
    if queue.current:
        loop_indicator = " 🔁" if queue.loop else ""
        embed.add_field(
            name="▶️ Now Playing",
            value=f"**{queue.current.title}**{loop_indicator}",
            inline=False
        )
    
    if queue.songs:
        queue_text = '\n'.join([f"`{i+1}.` {song.title}" 
                                for i, song in enumerate(queue.songs[:10])])
        if len(queue.songs) > 10:
            queue_text += f"\n*...and {len(queue.songs) - 10} more*"
        
        embed.add_field(
            name="📝 Up Next",
            value=queue_text,
            inline=False
        )
    
    return embed

def create_nowplaying_embed(song: Song, loop: bool) -> discord.Embed:
    """Create now playing embed"""
    loop_status = ' 🔁' if loop else ''
    
    embed = discord.Embed(
        title="🎵 Now Playing",
        description=f"**{song.title}**{loop_status}",
        color=discord.Color.green()
    )
    return embed

def create_playlist_list_embed(playlists: Dict[str, int]) -> discord.Embed:
    """Create playlist list embed"""
    embed = discord.Embed(
        title="📚 Available Playlists",
        color=discord.Color.blue()
    )
    
    for name, count in playlists.items():
        embed.add_field(
            name=name,
            value=f"{count} songs",
            inline=True
        )
    
    return embed

def create_playlist_show_embed(name: str, playlist: List[dict]) -> discord.Embed:
    """Create playlist details embed"""
    embed = discord.Embed(
        title=f"📚 Playlist: {name}",
        color=discord.Color.purple()
    )
    
    songs_text = '\n'.join([f"`{i+1}.` {item['title'][:60]}" 
                           for i, item in enumerate(playlist[:15])])
    if len(playlist) > 15:
        songs_text += f"\n*...and {len(playlist) - 15} more*"
    
    embed.description = songs_text
    return embed

def create_help_embed(bot_name: str) -> discord.Embed:
    """Create help command embed"""
    embed = discord.Embed(
        title="🎵 Music Bot Commands",
        description=f"Mention me with a command: `@{bot_name} <command>`",
        color=discord.Color.gold()
    )
    
    embed.add_field(
        name="🎵 Playback",
        value=(
            "`join` - Join your voice channel\n"
            "`leave` / `dc` - Leave voice channel\n"
            "`play <query>` / `p` - Play from YouTube or local file\n"
            "`search <query>` / `find` - Search YouTube\n"
            "`pause` - Pause playback\n"
            "`resume` - Resume playback\n"
            "`skip` / `next` / `s` - Skip current song\n"
            "`stop` - Stop and clear queue\n"
            "`loop` / `repeat` - Toggle loop mode\n"
            "`volume <0-100>` / `vol` - Adjust volume"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📝 Queue",
        value=(
            "`queue` / `q` - Show queue\n"
            "`nowplaying` / `np` - Show current song"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📚 Playlists",
        value=(
            "`playlist create <n>` - Create playlist\n"
            "`playlist add <n> <song>` - Add to playlist\n"
            "`playlist play <n>` - Play playlist\n"
            "`playlist list` - List all playlists\n"
            "`playlist show <n>` - Show playlist songs\n"
            "`playlist delete <n>` - Delete playlist (owner only)"
        ),
        inline=False
    )
    
    embed.add_field(
        name="💡 Examples",
        value=(
            f"`@{bot_name} play never gonna give you up`\n"
            f"`@{bot_name} play https://youtube.com/watch?v=...`\n"
            f"`@{bot_name} play C:/Music/song.mp3`\n"
            f"`@{bot_name} queue`"
        ),
        inline=False
    )
    
    embed.set_footer(text="Supports YouTube, local files, and 1000+ sites via yt-dlp")
    return embed