"""
Playlist management service - FIXED VERSION
FIX #9: File corruption risk - proper cleanup of temp files
FIX #17: Playlist name collision handling
"""
import json
import os
import tempfile
import shutil
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger('discord_bot')


class PlaylistServiceError(Exception):
    """Custom exception for playlist service errors"""
    pass


class PlaylistService:
    """
    Manages playlists with atomic file operations
    FIX #9: Ensures temp files are always cleaned up
    """
    
    def __init__(self, filepath: str = 'playlists.json') -> None:
        """
        Initialize playlist service
        
        Args:
            filepath: Path to playlists JSON file
        """
        self.filepath: str = filepath
        self.playlists: Dict[str, List[dict]] = {}
        self.load()
    
    def load(self) -> None:
        """Load playlists from file"""
        if not os.path.exists(self.filepath):
            logger.info(f"Playlist file not found, creating new: {self.filepath}")
            self.playlists = {}
            return
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.playlists = json.load(f)
            logger.info(f"Loaded {len(self.playlists)} playlists from {self.filepath}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse playlist file: {e}")
            # Backup corrupted file
            backup_path = f"{self.filepath}.backup"
            try:
                shutil.copy2(self.filepath, backup_path)
                logger.info(f"Backed up corrupted playlist file to {backup_path}")
            except Exception as backup_error:
                logger.error(f"Failed to backup corrupted file: {backup_error}")
            
            # Start with empty playlists
            self.playlists = {}
        except IOError as e:
            logger.error(f"Failed to read playlist file: {e}")
            raise PlaylistServiceError(f"Cannot read playlist file: {e}")
    
    def save(self) -> None:
        """
        Save playlists to file using atomic write operation
        
        FIX #9: Proper cleanup of temp files in all cases
        This prevents data corruption if the process is interrupted during write
        """
        tmp_filename = None
        
        try:
            # Create directory if it doesn't exist
            filepath_obj = Path(self.filepath)
            filepath_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to temporary file first (atomic operation)
            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                dir=filepath_obj.parent,
                delete=False,
                suffix='.tmp'
            ) as tmp_file:
                json.dump(self.playlists, tmp_file, indent=4, ensure_ascii=False)
                tmp_filename = tmp_file.name
            
            # Atomically replace the old file with the new one
            shutil.move(tmp_filename, self.filepath)
            tmp_filename = None  # Successfully moved, no cleanup needed
            logger.debug(f"Playlists saved to {self.filepath}")
            
        except (IOError, OSError) as e:
            logger.error(f"Failed to save playlists: {e}")
            raise PlaylistServiceError(f"Failed to save playlists: {e}")
        except json.JSONEncodeError as e:
            logger.error(f"Failed to encode playlists to JSON: {e}")
            raise PlaylistServiceError(f"Failed to encode playlists: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving playlists: {e}", exc_info=True)
            raise PlaylistServiceError(f"Unexpected error: {e}")
        finally:
            # FIX #9: Always cleanup temp file if it still exists
            if tmp_filename and os.path.exists(tmp_filename):
                try:
                    os.remove(tmp_filename)
                    logger.debug(f"Cleaned up temporary file: {tmp_filename}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temp file {tmp_filename}: {cleanup_error}")
    
    def create(self, name: str) -> bool:
        """
        Create a new playlist
        
        FIX #17: Case-insensitive name checking to prevent confusion
        
        Args:
            name: Playlist name
            
        Returns:
            True if created, False if already exists
        """
        # Validate name
        if not name or not name.strip():
            raise PlaylistServiceError("Playlist name cannot be empty")
        
        name = name.strip()
        
        # FIX #17: Check for case-insensitive duplicates
        name_lower = name.lower()
        for existing_name in self.playlists.keys():
            if existing_name.lower() == name_lower:
                logger.debug(f"Playlist '{name}' already exists (case-insensitive match with '{existing_name}')")
                return False
        
        self.playlists[name] = []
        self.save()
        logger.info(f"Created playlist '{name}'")
        return True
    
    def delete(self, name: str) -> bool:
        """
        Delete a playlist
        
        Args:
            name: Playlist name
            
        Returns:
            True if deleted, False if doesn't exist
        """
        if name not in self.playlists:
            logger.debug(f"Playlist '{name}' does not exist")
            return False
        
        del self.playlists[name]
        self.save()
        logger.info(f"Deleted playlist '{name}'")
        return True
    
    def add_song(self, playlist_name: str, song_data: dict, max_size: int = 500) -> bool:
        """
        Add a song to a playlist
        
        Args:
            playlist_name: Name of the playlist
            song_data: Song data dictionary
            max_size: Maximum playlist size (default from config)
            
        Returns:
            True if added, False if playlist doesn't exist or is full
        """
        if playlist_name not in self.playlists:
            logger.warning(f"Cannot add song: playlist '{playlist_name}' does not exist")
            return False
        
        # Check playlist size limit
        if len(self.playlists[playlist_name]) >= max_size:
            logger.warning(f"Playlist '{playlist_name}' is full (max {max_size} songs)")
            return False
        
        # Validate song data
        if not isinstance(song_data, dict):
            raise PlaylistServiceError("Song data must be a dictionary")
        
        self.playlists[playlist_name].append(song_data)
        self.save()
        logger.debug(f"Added song to playlist '{playlist_name}'")
        return True
    
    def remove_song(self, playlist_name: str, index: int) -> bool:
        """
        Remove a song from a playlist by index
        
        Args:
            playlist_name: Name of the playlist
            index: Index of the song to remove (0-based)
            
        Returns:
            True if removed, False if playlist doesn't exist or index invalid
        """
        if playlist_name not in self.playlists:
            logger.warning(f"Cannot remove song: playlist '{playlist_name}' does not exist")
            return False
        
        playlist = self.playlists[playlist_name]
        if not 0 <= index < len(playlist):
            logger.warning(f"Invalid index {index} for playlist '{playlist_name}'")
            return False
        
        removed_song = playlist.pop(index)
        self.save()
        logger.info(f"Removed song at index {index} from playlist '{playlist_name}'")
        return True
    
    def get_playlist(self, name: str) -> Optional[List[dict]]:
        """
        Get a playlist by name
        
        Args:
            name: Playlist name
            
        Returns:
            List of songs or None if doesn't exist
        """
        return self.playlists.get(name)
    
    def list_playlists(self) -> Dict[str, int]:
        """
        Get all playlists with song counts
        
        Returns:
            Dictionary mapping playlist names to song counts
        """
        return {name: len(songs) for name, songs in self.playlists.items()}
    
    def exists(self, name: str) -> bool:
        """
        Check if playlist exists
        
        Args:
            name: Playlist name
            
        Returns:
            True if exists, False otherwise
        """
        return name in self.playlists
    
    def clear_playlist(self, name: str) -> bool:
        """
        Clear all songs from a playlist
        
        Args:
            name: Playlist name
            
        Returns:
            True if cleared, False if doesn't exist
        """
        if name not in self.playlists:
            logger.warning(f"Cannot clear: playlist '{name}' does not exist")
            return False
        
        self.playlists[name].clear()
        self.save()
        logger.info(f"Cleared playlist '{name}'")
        return True
    
    def get_playlist_count(self) -> int:
        """
        Get total number of playlists
        
        Returns:
            Number of playlists
        """
        return len(self.playlists)


# Global playlist service instance
playlist_service = PlaylistService()
