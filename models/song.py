"""
Song and Queue data models
"""
from typing import List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class Song:
    """
    Represents a song in the queue
    
    Attributes:
        source: Audio source (file path or YTDLSource)
        title: Song title
        is_local: Whether the song is a local file
    """
    source: Any  # Can be file path (str) or YTDLSource
    title: str
    is_local: bool = False
    
    def __repr__(self) -> str:
        """String representation of the song"""
        return f"Song(title='{self.title}', is_local={self.is_local})"
    
    def __str__(self) -> str:
        """User-friendly string representation"""
        source_type = "Local" if self.is_local else "Stream"
        return f"{self.title} ({source_type})"


class MusicQueue:
    """
    Manages the music queue for a guild
    
    Attributes:
        songs: List of queued songs
        current: Currently playing song
        loop: Whether loop mode is enabled
        volume: Current volume (0.0 to 1.0)
    """
    
    # Constants
    DEFAULT_VOLUME = 0.5
    MIN_VOLUME = 0.0
    MAX_VOLUME = 1.0
    
    def __init__(self) -> None:
        """Initialize an empty music queue"""
        self.songs: List[Song] = []
        self.current: Optional[Song] = None
        self.loop: bool = False
        self._volume: float = self.DEFAULT_VOLUME
    
    @property
    def volume(self) -> float:
        """Get current volume"""
        return self._volume
    
    @volume.setter
    def volume(self, value: float) -> None:
        """
        Set volume with validation
        
        Args:
            value: Volume level (0.0 to 1.0)
        """
        if not isinstance(value, (int, float)):
            raise TypeError(f"Volume must be numeric, got {type(value).__name__}")
        
        # Clamp volume between min and max
        self._volume = max(self.MIN_VOLUME, min(self.MAX_VOLUME, float(value)))
    
    def add(self, song: Song) -> None:
        """
        Add a song to the queue
        
        Args:
            song: Song to add
        """
        if not isinstance(song, Song):
            raise TypeError(f"Expected Song object, got {type(song).__name__}")
        self.songs.append(song)
    
    def next(self) -> Optional[Song]:
        """
        Get the next song in queue
        
        Returns:
            Next song or None if queue is empty
        """
        if self.loop and self.current:
            return self.current
        
        if self.songs:
            self.current = self.songs.pop(0)
            return self.current
        
        return None
    
    def clear(self) -> None:
        """Clear the entire queue and current song"""
        self.songs.clear()
        self.current = None
    
    def remove(self, index: int) -> Optional[Song]:
        """
        Remove a song from the queue by index
        
        Args:
            index: Index of song to remove (0-based)
            
        Returns:
            Removed song or None if index invalid
        """
        if 0 <= index < len(self.songs):
            return self.songs.pop(index)
        return None
    
    def is_empty(self) -> bool:
        """
        Check if queue is empty
        
        Returns:
            True if no songs in queue and nothing playing
        """
        return len(self.songs) == 0 and self.current is None
    
    def get_upcoming(self, limit: int = 10) -> List[Song]:
        """
        Get upcoming songs in queue
        
        Args:
            limit: Maximum number of songs to return
            
        Returns:
            List of upcoming songs
        """
        return self.songs[:limit]
    
    def __len__(self) -> int:
        """
        Get queue length (excluding current song)
        
        Returns:
            Number of songs in queue
        """
        return len(self.songs)
    
    def __repr__(self) -> str:
        """String representation of the queue"""
        return f"MusicQueue(songs={len(self.songs)}, current={self.current}, loop={self.loop})"
    
    def __bool__(self) -> bool:
        """
        Check if queue has any songs
        
        Returns:
            True if queue is not empty
        """
        return not self.is_empty()
