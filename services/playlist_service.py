"""
Playlist management service
Handles loading, saving, and managing playlists
"""
import json
import os
from typing import Dict, List, Optional

class PlaylistService:
    """Manages playlists"""
    
    def __init__(self, filepath: str = 'playlists.json'):
        self.filepath = filepath
        self.playlists: Dict[str, List[dict]] = {}
        self.load()
    
    def load(self) -> None:
        """Load playlists from file"""
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r') as f:
                self.playlists = json.load(f)
        else:
            self.playlists = {}
    
    def save(self) -> None:
        """Save playlists to file"""
        with open(self.filepath, 'w') as f:
            json.dump(self.playlists, f, indent=4)
    
    def create(self, name: str) -> bool:
        """Create a new playlist"""
        if name in self.playlists:
            return False
        self.playlists[name] = []
        self.save()
        return True
    
    def delete(self, name: str) -> bool:
        """Delete a playlist"""
        if name not in self.playlists:
            return False
        del self.playlists[name]
        self.save()
        return True
    
    def add_song(self, playlist_name: str, song_data: dict) -> bool:
        """Add a song to a playlist"""
        if playlist_name not in self.playlists:
            return False
        self.playlists[playlist_name].append(song_data)
        self.save()
        return True
    
    def get_playlist(self, name: str) -> Optional[List[dict]]:
        """Get a playlist by name"""
        return self.playlists.get(name)
    
    def list_playlists(self) -> Dict[str, int]:
        """Get all playlists with song counts"""
        return {name: len(songs) for name, songs in self.playlists.items()}
    
    def exists(self, name: str) -> bool:
        """Check if playlist exists"""
        return name in self.playlists

# Global playlist service instance
playlist_service = PlaylistService()
