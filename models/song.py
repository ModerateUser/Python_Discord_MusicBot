"""
Song and Queue data models
"""
from typing import List, Optional, Any
from dataclasses import dataclass


@dataclass
class Song:
    """Represents a song in the queue"""
    source: Any  # Can be file path or YTDLSource
    title: str
    is_local: bool = False
    
    def __repr__(self) -> str:
        return f"Song(title='{self.title}', is_local={self.is_local})"


class MusicQueue:
    """Manages the music queue for a guild"""
    
    def __init__(self):
        self.songs: List[Song] = []
        self.current: Optional[Song] = None
        self.loop: bool = False
        self.volume: float = 0.5  # Default volume (50%)
    
    def add(self, song: Song) -> None:
        """Add a song to the queue"""
        self.songs.append(song)
    
    def next(self) -> Optional[Song]:
        """Get the next song in queue"""
        if self.loop and self.current:
            return self.current
        if self.songs:
            self.current = self.songs.pop(0)
            return self.current
        return None
    
    def clear(self) -> None:
        """Clear the entire queue"""
        self.songs.clear()
        self.current = None
    
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return len(self.songs) == 0 and self.current is None
    
    def __len__(self) -> int:
        """Get queue length"""
        return len(self.songs)
