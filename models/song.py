"""
Song and queue data models - FIXED VERSION
FIX #10: Volume property type coercion bug
"""
from typing import List, Optional, Any
import math

# Constants for volume control
DEFAULT_VOLUME = 0.5
MIN_VOLUME = 0.0
MAX_VOLUME = 1.0


class Song:
    """Represents a song in the queue"""
    
    def __init__(self, source: Any, title: str, is_local: bool = False):
        """
        Initialize a song
        
        Args:
            source: Audio source (YTDLSource or file path)
            title: Song title
            is_local: Whether this is a local file
        """
        self.source: Any = source
        self.title: str = title
        self.is_local: bool = is_local
    
    def __str__(self) -> str:
        """String representation of the song"""
        source_type = "Local" if self.is_local else "Stream"
        return f"{self.title} ({source_type})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return f"Song(title='{self.title}', is_local={self.is_local})"


class MusicQueue:
    """
    Manages the music queue for a guild
    FIX #10: Proper volume validation with finite number check
    """
    
    # Volume constants
    MIN_VOLUME = MIN_VOLUME
    MAX_VOLUME = MAX_VOLUME
    DEFAULT_VOLUME = DEFAULT_VOLUME
    
    def __init__(self):
        """Initialize an empty queue"""
        self.songs: List[Song] = []
        self.current: Optional[Song] = None
        self.loop: bool = False
        self._volume: float = self.DEFAULT_VOLUME
    
    @property
    def volume(self) -> float:
        """
        Get current volume
        
        Returns:
            Volume level (0.0 to 1.0)
        """
        return self._volume
    
    @volume.setter
    def volume(self, value: float) -> None:
        """
        Set volume with validation
        
        FIX #10: Check for finite numbers to prevent inf/nan
        
        Args:
            value: Volume level (0.0 to 1.0)
            
        Raises:
            TypeError: If value is not a number
            ValueError: If value is not finite (inf or nan)
        """
        if not isinstance(value, (int, float)):
            raise TypeError(f"Volume must be a number, got {type(value).__name__}")
        
        # FIX #10: Check for finite numbers
        if not math.isfinite(value):
            raise ValueError(f"Volume must be a finite number, got {value}")
        
        # Clamp to valid range
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
        Get the next song from the queue
        
        Returns:
            Next song or None if queue is empty
        """
        if self.loop and self.current:
            # Loop mode: return current song again
            return self.current
        
        if self.songs:
            self.current = self.songs.pop(0)
            return self.current
        
        self.current = None
        return None
    
    def clear(self) -> None:
        """Clear the queue and current song"""
        self.songs.clear()
        self.current = None
        self.loop = False
    
    def remove(self, index: int) -> Optional[Song]:
        """
        Remove a song at the specified index
        
        Args:
            index: Index of song to remove (0-based)
            
        Returns:
            Removed song or None if index is invalid
        """
        if 0 <= index < len(self.songs):
            return self.songs.pop(index)
        return None
    
    def get_upcoming(self, limit: int = 10) -> List[Song]:
        """
        Get upcoming songs in the queue
        
        Args:
            limit: Maximum number of songs to return
            
        Returns:
            List of upcoming songs
        """
        return self.songs[:limit]
    
    def __len__(self) -> int:
        """
        Get the number of songs in the queue
        
        Returns:
            Number of songs (not including current)
        """
        return len(self.songs)
    
    def __bool__(self) -> bool:
        """
        Check if queue has songs
        
        Returns:
            True if queue has songs or is currently playing
        """
        return bool(self.songs) or self.current is not None
    
    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return f"MusicQueue(songs={len(self.songs)}, current={self.current}, loop={self.loop}, volume={self._volume})"
