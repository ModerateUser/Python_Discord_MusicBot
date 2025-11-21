"""
Playlist management service
Handles loading, saving, and managing playlists with proper error handling
"""
import json
import os
from typing import Dict, List, Optional
import logging
from pathlib import Path

logger = logging.getLogger('discord_bot')


class PlaylistService:
    """Manages playlists with atomic file operations"""
    
    def __init__(self, filepath: str = 'playlists.json'):
        self.filepath = filepath
        self.playlists: Dict[str, List[dict]] = {}
        self.load()
    
    def load(self) -> None:
        """Load playlists from file with error handling"""
        if not os.path.exists(self.filepath):
            logger.info(f"Playlist file not found, creating new: {self.filepath}")
            self.playlists = {}
            self.save()  # Create the file
            return
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Validate loaded data
                if not isinstance(data, dict):
                    logger.error(f"Invalid playlist data format, expected dict got {type(data)}")
                    self.playlists = {}
                    return
                
                # Validate each playlist
                validated_playlists = {}
                for name, songs in data.items():
                    if not isinstance(songs, list):
                        logger.warning(f"Invalid playlist '{name}', expected list got {type(songs)}")
                        continue
                    validated_playlists[name] = songs
                
                self.playlists = validated_playlists
                logger.info(f"Loaded {len(self.playlists)} playlists")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse playlist file: {e}")
            # Backup corrupted file
            backup_path = f"{self.filepath}.backup"
            try:
                if os.path.exists(self.filepath):
                    os.rename(self.filepath, backup_path)
                    logger.info(f"Corrupted playlist file backed up to {backup_path}")
            except Exception as backup_error:
                logger.error(f"Failed to backup corrupted file: {backup_error}")
            
            self.playlists = {}
            self.save()  # Create fresh file
            
        except Exception as e:
            logger.error(f"Unexpected error loading playlists: {e}", exc_info=True)
            self.playlists = {}
    
    def save(self) -> bool:
        """
        Save playlists to file atomically
        Returns True on success, False on failure
        """
        temp_filepath = f"{self.filepath}.tmp"
        
        try:
            # Write to temporary file first
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                json.dump(self.playlists, f, indent=4, ensure_ascii=False)
            
            # Atomic rename (on most systems)
            if os.path.exists(self.filepath):
                # Create backup before replacing
                backup_path = f"{self.filepath}.bak"
                try:
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    os.rename(self.filepath, backup_path)
                except Exception as e:
                    logger.warning(f"Failed to create backup: {e}")
            
            os.rename(temp_filepath, self.filepath)
            logger.debug(f"Playlists saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save playlists: {e}", exc_info=True)
            
            # Cleanup temp file if it exists
            try:
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
            except Exception:
                pass
            
            return False
    
    def create(self, name: str) -> bool:
        """
        Create a new playlist
        Returns True if created, False if already exists
        """
        if not name or not isinstance(name, str):
            logger.warning(f"Invalid playlist name: {name}")
            return False
        
        if name in self.playlists:
            return False
        
        self.playlists[name] = []
        
        if self.save():
            logger.info(f"Created playlist: {name}")
            return True
        else:
            # Rollback on save failure
            del self.playlists[name]
            return False
    
    def delete(self, name: str) -> bool:
        """
        Delete a playlist
        Returns True if deleted, False if doesn't exist
        """
        if name not in self.playlists:
            return False
        
        # Keep backup for rollback
        backup = self.playlists[name].copy()
        del self.playlists[name]
        
        if self.save():
            logger.info(f"Deleted playlist: {name}")
            return True
        else:
            # Rollback on save failure
            self.playlists[name] = backup
            return False
    
    def add_song(self, playlist_name: str, song_data: dict) -> bool:
        """
        Add a song to a playlist
        Returns True if added, False if playlist doesn't exist or save fails
        """
        if playlist_name not in self.playlists:
            logger.warning(f"Attempted to add song to non-existent playlist: {playlist_name}")
            return False
        
        if not isinstance(song_data, dict):
            logger.warning(f"Invalid song data type: {type(song_data)}")
            return False
        
        # Validate song data has required fields
        required_fields = ['type', 'path', 'title']
        if not all(field in song_data for field in required_fields):
            logger.warning(f"Song data missing required fields: {song_data}")
            return False
        
        self.playlists[playlist_name].append(song_data)
        
        if self.save():
            logger.debug(f"Added song to playlist '{playlist_name}': {song_data.get('title', 'unknown')}")
            return True
        else:
            # Rollback on save failure
            self.playlists[playlist_name].pop()
            return False
    
    def remove_song(self, playlist_name: str, index: int) -> bool:
        """
        Remove a song from a playlist by index
        Returns True if removed, False if playlist doesn't exist or index invalid
        """
        if playlist_name not in self.playlists:
            return False
        
        playlist = self.playlists[playlist_name]
        
        if not 0 <= index < len(playlist):
            logger.warning(f"Invalid song index {index} for playlist '{playlist_name}'")
            return False
        
        # Keep backup for rollback
        removed_song = playlist.pop(index)
        
        if self.save():
            logger.info(f"Removed song from playlist '{playlist_name}': {removed_song.get('title', 'unknown')}")
            return True
        else:
            # Rollback on save failure
            playlist.insert(index, removed_song)
            return False
    
    def get_playlist(self, name: str) -> Optional[List[dict]]:
        """
        Get a playlist by name
        Returns list of songs or None if doesn't exist
        """
        return self.playlists.get(name)
    
    def list_playlists(self) -> Dict[str, int]:
        """
        Get all playlists with song counts
        Returns dict of {playlist_name: song_count}
        """
        return {name: len(songs) for name, songs in self.playlists.items()}
    
    def exists(self, name: str) -> bool:
        """Check if playlist exists"""
        return name in self.playlists
    
    def get_total_songs(self, name: str) -> int:
        """Get total number of songs in a playlist"""
        playlist = self.get_playlist(name)
        return len(playlist) if playlist else 0
    
    def clear_playlist(self, name: str) -> bool:
        """
        Clear all songs from a playlist
        Returns True if cleared, False if doesn't exist or save fails
        """
        if name not in self.playlists:
            return False
        
        # Keep backup for rollback
        backup = self.playlists[name].copy()
        self.playlists[name] = []
        
        if self.save():
            logger.info(f"Cleared playlist: {name}")
            return True
        else:
            # Rollback on save failure
            self.playlists[name] = backup
            return False


# Global playlist service instance
playlist_service = PlaylistService()
