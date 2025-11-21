"""
Discord embed creation utilities with consistent styling - FIXED VERSION
FIX #14: Embed field length validation to prevent Discord API errors
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

# FIX #14: Discord embed limits
DISCORD_EMBED_TITLE_LIMIT = 256
DISCORD_EMBED_DESCRIPTION_LIMIT = 4096
DISCORD_EMBED_FIELD_NAME_LIMIT = 256
DISCORD_EMBED_FIELD_VALUE_LIMIT = 1024
DISCORD_EMBED_FOOTER_LIMIT = 2048
DISCORD_EMBED_TOTAL_LIMIT = 6000


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to fit within Discord limits
    
    FIX #14: Helper function for safe text truncation
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def create_search_embed(query: str, results: List[dict], bot_name: str) -> discord.Embed:
    """
    Create search results embed
    
    FIX #14: Validate all field lengths
    
    Args:
        query: Search query string
        results: List of search result dictionaries
        bot_name: Name of the bot
        
    Returns:
        Discord embed with search results
    """
    # FIX #14: Truncate title to Discord limit
    title = truncate_text(f"🔍 Search Results for: {query}", DISCORD_EMBED_TITLE_LIMIT)
    
    embed = discord.Embed(
        title=title,
        color=COLOR_SEARCH
    )
    
    for i, result in enumerate(results[:MAX_SEARCH_RESULTS], 1):
        title = result.get('title', 'Unknown')
        # FIX #14: Truncate field name
        field_name = truncate_text(f"{i}. {title}", DISCORD_EMBED_FIELD_NAME_LIMIT)
        
        duration = result.get('duration', 0)
        
        # Format duration
        if duration:
            mins, secs = divmod(duration, 60)
            duration_str = f"{mins}:{secs:02d}"
        else:
            duration_str = "Unknown"
        
        # FIX #14: Truncate field value
        field_value = truncate_text(f"Duration: {duration_str}", DISCORD_EMBED_FIELD_VALUE_LIMIT)
        
        embed.add_field(
            name=field_name,
            value=field_value,
            inline=False
        )
    
    # FIX #14: Truncate footer
    footer_text = truncate_text(f"Use @{bot_name} play <song name> to play", DISCORD_EMBED_FOOTER_LIMIT)
    embed.set_footer(text=footer_text)
    return embed


def create_queue_embed(queue: MusicQueue) -> discord.Embed:
    """
    Create queue display embed
    
    FIX #14: Validate all field lengths
    
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
        # FIX #14: Truncate current song title
        current_title = truncate_text(queue.current.title, DISCORD_EMBED_FIELD_VALUE_LIMIT - 20)
        embed.add_field(
            name="▶️ Now Playing",
            value=f"**{current_title}**{loop_indicator}",
            inline=False
        )
    
    # Show upcoming songs
    if queue.songs:
        queue_lines = []
        for i, song in enumerate(queue.songs[:MAX_QUEUE_DISPLAY]):
            # FIX #14: Truncate each song title
            song_title = truncate_text(song.title, MAX_TITLE_LENGTH)
            queue_lines.append(f"`{i+1}.` {song_title}")
        
        queue_text = '\n'.join(queue_lines)
        
        if len(queue.songs) > MAX_QUEUE_DISPLAY:
            queue_text += f"\n*...and {len(queue.songs) - MAX_QUEUE_DISPLAY} more*"
        
        # FIX #14: Ensure total queue text fits in field value limit
        queue_text = truncate_text(queue_text, DISCORD_EMBED_FIELD_VALUE_LIMIT)
        
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
    
    FIX #14: Validate all field lengths
    
    Args:
        song: Currently playing song
        loop: Whether loop mode is enabled
        
    Returns:
        Discord embed showing now playing info
    """
    loop_status = ' 🔁' if loop else ''
    source_type = '📁 Local File' if song.is_local else '🌐 Stream'
    
    # FIX #14: Truncate song title for description
    song_title = truncate_text(song.title, DISCORD_EMBED_DESCRIPTION_LIMIT - 10)
    
    embed = discord.Embed(
        title="🎵 Now Playing",
        description=f"**{song_title}**{loop_status}",
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
    
    FIX #14: Validate all field lengths
    
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
    
    # FIX #14: Track total embed size to prevent exceeding limits
    total_chars = len(embed.title or "") + len(embed.description or "")
    
    for name, count in sorted_playlists:
        song_text = "song" if count == 1 else "songs"
        
        # FIX #14: Truncate playlist name
        playlist_name = truncate_text(name, DISCORD_EMBED_FIELD_NAME_LIMIT - 5)
        field_value = f"{count} {song_text}"
        
        # FIX #14: Check if adding this field would exceed total limit
        field_size = len(playlist_name) + len(field_value)
        if total_chars + field_size > DISCORD_EMBED_TOTAL_LIMIT - 500:  # Leave buffer
            embed.add_field(
                name="⚠️ Note",
                value=f"...and {len(sorted_playlists) - len(embed.fields)} more playlists",
                inline=False
            )
            break
        
        embed.add_field(
            name=f"📁 {playlist_name}",
            value=field_value,
            inline=True
        )
        total_chars += field_size
    
    return embed


def create_playlist_show_embed(name: str, playlist: List[dict]) -> discord.Embed:
    """
    Create playlist details embed
    
    FIX #14: Validate all field lengths
    
    Args:
        name: Playlist name
        playlist: List of song dictionaries
        
    Returns:
        Discord embed showing playlist contents
    """
    # FIX #14: Truncate playlist name in title
    playlist_name = truncate_text(name, DISCORD_EMBED_TITLE_LIMIT - 15)
    
    embed = discord.Embed(
        title=f"📚 Playlist: {playlist_name}",
        description=f"Total songs: {len(playlist)}",
        color=COLOR_PLAYLIST
    )
    
    if not playlist:
        embed.description = "This playlist is empty. Add songs with `!playlist add <name> <song>`"
        return embed
    
    songs_lines = []
    for i, item in enumerate(playlist[:MAX_PLAYLIST_DISPLAY]):
        # FIX #14: Truncate each song title
        song_title = truncate_text(item.get('title', 'Unknown'), MAX_TITLE_LENGTH)
        songs_lines.append(f"`{i+1}.` {song_title}")
    
    songs_text = '\n'.join(songs_lines)
    
    if len(playlist) > MAX_PLAYLIST_DISPLAY:
        songs_text += f"\n*...and {len(playlist) - MAX_PLAYLIST_DISPLAY} more*"
    
    # FIX #14: Ensure songs text fits in field value limit
    songs_text = truncate_text(songs_text, DISCORD_EMBED_FIELD_VALUE_LIMIT)
    
    embed.add_field(
        name="Songs",
        value=songs_text,
        inline=False
    )
    
    return embed


def create_help_embed(bot_name: str) -> discord.Embed:
    """
    Create help command embed
    
    FIX #14: Validate all field lengths
    
    Args:
        bot_name: Name of the bot
        
    Returns:
        Discord embed with command help
    """
    # FIX #14: Truncate bot name in description
    bot_name_safe = truncate_text(bot_name, 50)
    description = truncate_text(
        f"Mention me with a command: `@{bot_name_safe} <command>` or use `!<command>`",
        DISCORD_EMBED_DESCRIPTION_LIMIT
    )
    
    embed = discord.Embed(
        title="🎵 Music Bot Commands",
        description=description,
        color=COLOR_HELP
    )
    
    # FIX #14: All field values are within limits (pre-validated)
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
    
    # FIX #14: Truncate examples with bot name
    examples_text = truncate_text(
        f"`@{bot_name_safe} play never gonna give you up`\n"
        f"`!play https://youtube.com/watch?v=...`\n"
        f"`!play C:/Music/song.mp3`\n"
        f"`!queue`",
        DISCORD_EMBED_FIELD_VALUE_LIMIT
    )
    
    embed.add_field(
        name="💡 Examples",
        value=examples_text,
        inline=False
    )
    
    embed.set_footer(text="Supports YouTube, local files, and 1000+ sites via yt-dlp")
    return embed


def create_error_embed(title: str, message: str) -> discord.Embed:
    """
    Create error message embed
    
    FIX #14: Validate all field lengths
    
    Args:
        title: Error title
        message: Error message
        
    Returns:
        Discord embed for error display
    """
    # FIX #14: Truncate title and message
    safe_title = truncate_text(f"❌ {title}", DISCORD_EMBED_TITLE_LIMIT)
    safe_message = truncate_text(message, DISCORD_EMBED_DESCRIPTION_LIMIT)
    
    embed = discord.Embed(
        title=safe_title,
        description=safe_message,
        color=discord.Color.red()
    )
    return embed


def create_success_embed(title: str, message: str) -> discord.Embed:
    """
    Create success message embed
    
    FIX #14: Validate all field lengths
    
    Args:
        title: Success title
        message: Success message
        
    Returns:
        Discord embed for success display
    """
    # FIX #14: Truncate title and message
    safe_title = truncate_text(f"✅ {title}", DISCORD_EMBED_TITLE_LIMIT)
    safe_message = truncate_text(message, DISCORD_EMBED_DESCRIPTION_LIMIT)
    
    embed = discord.Embed(
        title=safe_title,
        description=safe_message,
        color=discord.Color.green()
    )
    return embed
