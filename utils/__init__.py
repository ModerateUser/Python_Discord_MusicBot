"""
Utils package for Discord Music Bot
Contains utility functions and helpers
"""

from .logger import setup_logger
from .embeds import (
    create_search_embed,
    create_queue_embed,
    create_nowplaying_embed,
    create_playlist_list_embed,
    create_playlist_show_embed,
    create_help_embed
)

__all__ = [
    'setup_logger',
    'create_search_embed',
    'create_queue_embed',
    'create_nowplaying_embed',
    'create_playlist_list_embed',
    'create_playlist_show_embed',
    'create_help_embed'
]
