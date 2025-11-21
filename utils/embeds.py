"""
Discord embed utilities for consistent formatting
"""
import discord
from typing import Optional


def create_music_embed(title: str, description: str = None, color: discord.Color = discord.Color.blue()) -> discord.Embed:
    """
    Create a music-themed embed
    
    Args:
        title: Embed title
        description: Embed description (optional)
        color: Embed color (default: blue)
    
    Returns:
        discord.Embed: Formatted embed
    """
    embed = discord.Embed(title=f'🎵 {title}', color=color)
    if description:
        embed.description = description
    return embed


def create_error_embed(message: str) -> discord.Embed:
    """
    Create an error embed
    
    Args:
        message: Error message
    
    Returns:
        discord.Embed: Error embed with red color
    """
    embed = discord.Embed(
        title='❌ Error',
        description=message,
        color=discord.Color.red()
    )
    return embed


def create_success_embed(message: str) -> discord.Embed:
    """
    Create a success embed
    
    Args:
        message: Success message
    
    Returns:
        discord.Embed: Success embed with green color
    """
    embed = discord.Embed(
        title='✅ Success',
        description=message,
        color=discord.Color.green()
    )
    return embed


def create_queue_embed(queue: list, current_song: Optional[dict] = None) -> discord.Embed:
    """
    Create an embed showing the music queue
    
    Args:
        queue: List of songs in queue
        current_song: Currently playing song (optional)
    
    Returns:
        discord.Embed: Queue embed
    """
    embed = discord.Embed(
        title='🎵 Music Queue',
        color=discord.Color.blue()
    )
    
    if current_song:
        embed.add_field(
            name='Now Playing',
            value=f'**{current_song.get("title", "Unknown")}**',
            inline=False
        )
    
    if queue:
        queue_text = '\n'.join([
            f'{i+1}. {song.get("title", "Unknown")}'
            for i, song in enumerate(queue[:10])  # Show first 10
        ])
        
        if len(queue) > 10:
            queue_text += f'\n\n*...and {len(queue) - 10} more*'
        
        embed.add_field(
            name=f'Up Next ({len(queue)} songs)',
            value=queue_text,
            inline=False
        )
    else:
        embed.add_field(
            name='Queue',
            value='*Queue is empty*',
            inline=False
        )
    
    return embed


def create_nowplaying_embed(song: dict, volume: int = 50, loop: bool = False) -> discord.Embed:
    """
    Create an embed for the currently playing song
    
    Args:
        song: Song dictionary with metadata
        volume: Current volume (0-100)
        loop: Whether loop mode is enabled
    
    Returns:
        discord.Embed: Now playing embed
    """
    embed = discord.Embed(
        title='🎵 Now Playing',
        description=f'**{song.get("title", "Unknown")}**',
        color=discord.Color.blue()
    )
    
    if song.get('uploader'):
        embed.add_field(name='Uploader', value=song['uploader'], inline=True)
    
    if song.get('duration'):
        minutes, seconds = divmod(song['duration'], 60)
        embed.add_field(name='Duration', value=f'{int(minutes)}:{int(seconds):02d}', inline=True)
    
    embed.add_field(name='Volume', value=f'{volume}%', inline=True)
    
    if loop:
        embed.add_field(name='Loop', value='🔁 Enabled', inline=True)
    
    if song.get('thumbnail'):
        embed.set_thumbnail(url=song['thumbnail'])
    
    if song.get('webpage_url'):
        embed.add_field(name='URL', value=f'[Link]({song["webpage_url"]})', inline=False)
    
    return embed
