"""
Discord embed creation utilities with consistent styling
"""
import discord
from typing import List, Dict
from models.song import Song, MusicQueue

# Constants for embed colors
COLOR_SEARCH = discord.Color.blue()
COLOR_QUEUE = discord.Color.purple()
COLOR_NOW_PLAYING = discord.Color.green()
COLOR_PLAYLIST = discord.Color.blue()
COLOR_HELP = discord.Color.gold()

# Constants for display limits
MAX_SEARCH_RESULTS = 5
MAX_QUEUE_DISPLAY = 10
MAX_PLAYLIST_DISPLAY = 15
MAX_TITLE_LENGTH = 60


def create_search_embed(query: str, results: List[dict], bot_name: str) -> discord.Embed:
    """
    Create search results embed
    
    Args:
        query: Search query string
        results: List of search result dictionaries
        bot_name: Name of the bot
        
    Returns:
        Discord embed with search results
    """
    embed = discord.Embed(
        title=f"🔍 Search Results for: {query[:100]}",
        color=COLOR_SEARCH
    )
    
    for i, result in enumerate(results[:MAX_SEARCH_RESULTS], 1):
        title = result.get('title', 'Unknown')[:MAX_TITLE_LENGTH]
        duration = result.get('duration', 0)
        
        # Format duration
        if duration:
            mins, secs = divmod(duration, 60)
            duration_str = f"{mins}:{secs:02d}"
        else:
            duration_str = "Unknown"
        
        embed.add_field(
            name=f"{i}. {title}",
            value=f"Duration: {duration_str}",
            inline=False
        )
    
    embed.set_footer(text=f"Use @{bot_name} play <song name> to play")
    return embed


def create_queue_embed(queue: MusicQueue) -> discord.Embed:
    """
    Create queue display embed
    
    Args:
        queue: MusicQueue instance
        
    Returns:
        Discord embed showing current queue
    """
    embed = discord.Embed(
        title="🎵 Music Queue",
        color=COLOR_QUEUE
    )
    
    # Show currently playing song
    if queue.current:
        loop_indicator = " 🔁" if queue.loop else ""
        embed.add_field(
            name="▶️ Now Playing",
            value=f"**{queue.current.title}**{loop_indicator}",
            inline=False
        )
    
    # Show upcoming songs
    if queue.songs:
        queue_text = '\n'.join([
            f"`{i+1}.` {song.title[:MAX_TITLE_LENGTH]}" 
            for i, song in enumerate(queue.songs[:MAX_QUEUE_DISPLAY])
        ])
        
        if len(queue.songs) > MAX_QUEUE_DISPLAY:
            queue_text += f"\n*...and {len(queue.songs) - MAX_QUEUE_DISPLAY} more*"
        
        embed.add_field(
            name=f"📝 Up Next ({len(queue.songs)} songs)",
            value=queue_text,
            inline=False
        )
    
    # Show volume
    volume_percent = int(queue.volume * 100)
    embed.add_field(
        name="🔊 Volume",
        value=f"{volume_percent}%",
        inline=True
    )
    
    return embed


def create_nowplaying_embed(song: Song, loop: bool) -> discord.Embed:
    """
    Create now playing embed
    
    Args:
        song: Currently playing song
        loop: Whether loop mode is enabled
        
    Returns:
        Discord embed showing now playing info
    """
    loop_status = ' 🔁' if loop else ''
    source_type = '📁 Local File' if song.is_local else '🌐 Stream'
    
    embed = discord.Embed(
        title="🎵 Now Playing",
        description=f"**{song.title}**{loop_status}",
        color=COLOR_NOW_PLAYING
    )
    
    embed.add_field(
        name="Source",
        value=source_type,
        inline=True
    )
    
    return embed


def create_playlist_list_embed(playlists: Dict[str, int]) -> discord.Embed:
    """
    Create playlist list embed
    
    Args:
        playlists: Dictionary mapping playlist names to song counts
        
    Returns:
        Discord embed showing all playlists
    """
    embed = discord.Embed(
        title="📚 Available Playlists",
        description=f"Total playlists: {len(playlists)}",
        color=COLOR_PLAYLIST
    )
    
    if not playlists:
        embed.description = "No playlists available. Create one with `!playlist create <name>`"
        return embed
    
    # Sort playlists by name
    sorted_playlists = sorted(playlists.items())
    
    for name, count in sorted_playlists:
        song_text = "song" if count == 1 else "songs"
        embed.add_field(
            name=f"📁 {name}",
            value=f"{count} {song_text}",
            inline=True
        )
    
    return embed


def create_playlist_show_embed(name: str, playlist: List[dict]) -> discord.Embed:
    """
    Create playlist details embed
    
    Args:
        name: Playlist name
        playlist: List of song dictionaries
        
    Returns:
        Discord embed showing playlist contents
    """
    embed = discord.Embed(
        title=f"📚 Playlist: {name}",
        description=f"Total songs: {len(playlist)}",
        color=COLOR_PLAYLIST
    )
    
    if not playlist:
        embed.description = "This playlist is empty. Add songs with `!playlist add <name> <song>`"
        return embed
    
    songs_text = '\n'.join([
        f"`{i+1}.` {item.get('title', 'Unknown')[:MAX_TITLE_LENGTH]}" 
        for i, item in enumerate(playlist[:MAX_PLAYLIST_DISPLAY])
    ])
    
    if len(playlist) > MAX_PLAYLIST_DISPLAY:
        songs_text += f"\n*...and {len(playlist) - MAX_PLAYLIST_DISPLAY} more*"
    
    embed.add_field(
        name="Songs",
        value=songs_text,
        inline=False
    )
    
    return embed


def create_help_embed(bot_name: str) -> discord.Embed:
    """
    Create help command embed
    
    Args:
        bot_name: Name of the bot
        
    Returns:
        Discord embed with command help
    """
    embed = discord.Embed(
        title="🎵 Music Bot Commands",
        description=f"Mention me with a command: `@{bot_name} <command>` or use `!<command>`",
        color=COLOR_HELP
    )
    
    embed.add_field(
        name="🎵 Playback Commands",
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
        name="📝 Queue Commands",
        value=(
            "`queue` / `q` - Show queue\n"
            "`nowplaying` / `np` - Show current song"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📚 Playlist Commands",
        value=(
            "`playlist create <name>` - Create playlist\n"
            "`playlist add <name> <song>` - Add to playlist\n"
            "`playlist play <name>` - Play playlist\n"
            "`playlist list` - List all playlists\n"
            "`playlist show <name>` - Show playlist songs\n"
            "`playlist delete <name>` - Delete playlist (owner only)"
        ),
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ Other Commands",
        value=(
            "`ping` - Check bot latency\n"
            "`info` - Show bot information\n"
            "`help` - Show this help message"
        ),
        inline=False
    )
    
    embed.add_field(
        name="💡 Examples",
        value=(
            f"`@{bot_name} play never gonna give you up`\n"
            f"`!play https://youtube.com/watch?v=...`\n"
            f"`!play C:/Music/song.mp3`\n"
            f"`!queue`"
        ),
        inline=False
    )
    
    embed.set_footer(text="Supports YouTube, local files, and 1000+ sites via yt-dlp")
    return embed


def create_error_embed(title: str, message: str) -> discord.Embed:
    """
    Create error message embed
    
    Args:
        title: Error title
        message: Error message
        
    Returns:
        Discord embed for error display
    """
    embed = discord.Embed(
        title=f"❌ {title}",
        description=message,
        color=discord.Color.red()
    )
    return embed


def create_success_embed(title: str, message: str) -> discord.Embed:
    """
    Create success message embed
    
    Args:
        title: Success title
        message: Success message
        
    Returns:
        Discord embed for success display
    """
    embed = discord.Embed(
        title=f"✅ {title}",
        description=message,
        color=discord.Color.green()
    )
    return embed
