#!/usr/bin/env python3
"""
Playlist Manager Component
Handles playlist creation, modification, and persistence
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union

# Default playlist file location
DEFAULT_PLAYLISTS_FILE = os.path.expanduser("~/.config/chromecast_playlists.json")

class PlaylistManager:
    """
    Manage playlists for Chromecast devices.
    Handles playlist creation, modification, and persistence.
    """
    
    def __init__(self, playlists_file: str = DEFAULT_PLAYLISTS_FILE):
        """Initialize the PlaylistManager."""
        self.playlists_file = playlists_file
        
        # Create the parent directory if it doesn't exist
        os.makedirs(os.path.dirname(self.playlists_file), exist_ok=True)
        
        # Load existing playlists
        self._load_playlists()
        
    def _load_playlists(self):
        """Load playlists from JSON file."""
        if os.path.exists(self.playlists_file):
            try:
                with open(self.playlists_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.playlists = data
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading playlists: {e}")
                self.playlists = {}
                # Create a new empty playlists file
                self._save_playlists()
        else:
            # Create a new empty playlists file
            self.playlists = {}
            self._save_playlists()
        
        return self.playlists
    def _save_playlists(self):
        """Save playlists to JSON file."""
        try:
            with open(self.playlists_file, 'w', encoding='utf-8') as f:
                json.dump(self.playlists, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving playlists: {e}")
            return False
            
    def get_playlists(self) -> List[str]:
        """
        Get a list of available playlist names.
        
        Returns:
            List of playlist names
        """
        return list(self.playlists.keys())
        
    def create_playlist(self, name: str) -> bool:
        """
        Create a new playlist.
        
        Args:
            name: Name of the playlist
            
        Returns:
            True if successful, False otherwise
        """
        if name in self.playlists:
            print(f"Playlist '{name}' already exists")
            return False
            
        self.playlists[name] = []
        return self._save_playlists()
        
    def delete_playlist(self, name: str) -> bool:
        """
        Delete a playlist.
        
        Args:
            name: Name of the playlist
            
        Returns:
            True if successful, False otherwise
        """
        if name not in self.playlists:
            print(f"Playlist '{name}' does not exist")
            return False
            
        del self.playlists[name]
        return self._save_playlists()
        
    def get_playlist(self, name: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get the contents of a playlist.
        
        Args:
            name: Name of the playlist
            
        Returns:
            List of playlist items or None if playlist doesn't exist
        """
        return self.playlists.get(name)
        
    def add_to_playlist(self, playlist_name: str, url: str, title: str = None) -> bool:
        """
        Add a media item to a playlist.
        
        Args:
            playlist_name: Name of the playlist
            url: URL of the media
            title: Title of the media (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if playlist_name not in self.playlists:
            print(f"Playlist '{playlist_name}' does not exist")
            return False
            
        if not title:
            title = os.path.basename(url)
            
        item = {
            "url": url,
            "title": title,
            "added": time.time()
        }
        
        self.playlists[playlist_name].append(item)
        return self._save_playlists()
        
    def remove_from_playlist(self, playlist_name: str, index: int) -> bool:
        """
        Remove an item from a playlist.
        
        Args:
            playlist_name: Name of the playlist
            index: Index of the item to remove
            
        Returns:
            True if successful, False otherwise
        """
        if playlist_name not in self.playlists:
            print(f"Playlist '{playlist_name}' does not exist")
            return False
            
        if index < 0 or index >= len(self.playlists[playlist_name]):
            print(f"Invalid index {index} for playlist '{playlist_name}'")
            return False
            
        self.playlists[playlist_name].pop(index)
        return self._save_playlists()
