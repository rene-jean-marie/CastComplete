#!/usr/bin/env python3
"""
Chromecast Manager
Main interface combining playlist, device, and media player functionality
"""

from typing import Dict, List, Optional, Any, Tuple, Union

from .playlist_manager import PlaylistManager
from .device_manager import DeviceManager
from .media_player import MediaPlayer

# Default playlist file location
import os
DEFAULT_PLAYLISTS_FILE = os.path.expanduser("~/.config/chromecast_playlists.json")

class ChromecastManager:
    """
    Main interface for the Chromecast Web Playlist Manager.
    Combines playlist management, device management, and media playback functionality.
    """
    
    def __init__(self, playlists_file: str = DEFAULT_PLAYLISTS_FILE):
        """
        Initialize the ChromecastManager.
        
        Args:
            playlists_file: Path to the playlists JSON file
        """
        self.playlist_manager = PlaylistManager(playlists_file)
        self.device_manager = DeviceManager()
        self.media_player = MediaPlayer(self.playlist_manager, self.device_manager)
        
        # Forward properties from components for backward compatibility
        self.playlists = self.playlist_manager.playlists
        self.playlists_file = self.playlist_manager.playlists_file
        self.connected_devices = self.device_manager.connected_devices
        self.media_controllers = self.device_manager.media_controllers
        self.device_statuses = self.device_manager.device_statuses
        self.device_groups = self.device_manager.device_groups
        self.chromecast = self.device_manager.chromecast
        self.media_controller = self.device_manager.media_controller
        self.active_device = self.device_manager.active_device
        self.current_playlist = self.media_player.current_playlist
        self.current_index = self.media_player.current_index
        
        # Web client support
        self.web_clients = self.device_manager.web_clients
        self.all_devices = self.device_manager.all_devices
        
    # --- Playlist Management Methods ---
    
    def get_playlists(self) -> List[str]:
        """Get a list of available playlist names."""
        return self.playlist_manager.get_playlists()
        
    def create_playlist(self, name: str) -> bool:
        """Create a new playlist."""
        return self.playlist_manager.create_playlist(name)
        
    def delete_playlist(self, name: str) -> bool:
        """Delete a playlist."""
        return self.playlist_manager.delete_playlist(name)
        
    def get_playlist(self, name: str) -> Optional[List[Dict[str, Any]]]:
        """Get the contents of a playlist."""
        return self.playlist_manager.get_playlist(name)
        
    def add_to_playlist(self, playlist_name: str, url: str, title: str = None) -> bool:
        """Add a media item to a playlist."""
        return self.playlist_manager.add_to_playlist(playlist_name, url, title)
        
    def remove_from_playlist(self, playlist_name: str, index: int) -> bool:
        """Remove an item from a playlist."""
        return self.playlist_manager.remove_from_playlist(playlist_name, index)
        
    # --- Device Management Methods ---
    
    def discover_devices(self) -> List[str]:
        """Discover available Chromecast devices on the network."""
        return self.device_manager.discover_devices()
        
    def connect(self, device_name: str) -> bool:
        """Connect to a Chromecast device."""
        result = self.device_manager.connect(device_name)
        # Update references after connection
        self.chromecast = self.device_manager.chromecast
        self.media_controller = self.device_manager.media_controller
        self.active_device = self.device_manager.active_device
        return result
        
    def disconnect(self, device_name: str = None) -> bool:
        """Disconnect from a Chromecast device."""
        result = self.device_manager.disconnect(device_name)
        # Update references after disconnection
        self.chromecast = self.device_manager.chromecast
        self.media_controller = self.device_manager.media_controller
        self.active_device = self.device_manager.active_device
        return result
        
    def get_device_groups(self) -> Dict[str, List[str]]:
        """Get all device groups."""
        return self.device_manager.device_groups.copy()
        
    # --- Web Client Management Methods ---
    
    def register_web_client(self, client_id: str, client_info: Dict[str, Any]) -> bool:
        """Register a web client as a device."""
        return self.device_manager.register_web_client(client_id, client_info)
    
    def update_web_client(self, client_id: str, status_update: Dict[str, Any]) -> bool:
        """Update the status of a web client."""
        return self.device_manager.update_web_client(client_id, status_update)
    
    def remove_web_client(self, client_id: str) -> bool:
        """Remove a web client."""
        return self.device_manager.remove_web_client(client_id)
        
    def get_all_devices(self) -> List[str]:
        """Get all connected devices (Chromecasts, web clients, and groups)."""
        return self.device_manager.get_all_devices()
        
    def create_device_group(self, name: str, device_names: List[str] = None) -> bool:
        """Create a new device group."""
        return self.device_manager.create_device_group(name, device_names)
        
    def delete_device_group(self, name: str) -> bool:
        """Delete a device group."""
        return self.device_manager.delete_device_group(name)
        
    def add_to_device_group(self, group_name: str, device_name: str) -> bool:
        """Add a device to a group."""
        return self.device_manager.add_to_device_group(group_name, device_name)
        
    def remove_from_device_group(self, group_name: str, device_name: str) -> bool:
        """Remove a device from a group."""
        return self.device_manager.remove_from_device_group(group_name, device_name)
        
    def sync_device_group(self, group_name: str) -> bool:
        """Synchronize playback across devices in a group."""
        return self.device_manager.sync_device_group(group_name)
        
    # --- Media Playback Methods ---
    
    def load_playlist(self, playlist_name: str, target: Union[str, List[str]] = None) -> bool:
        """Load a playlist for playback."""
        result = self.media_player.load_playlist(playlist_name, target)
        # Update references
        self.current_playlist = self.media_player.current_playlist
        self.current_index = self.media_player.current_index
        return result
        
    def play(self, target: Union[str, List[str]] = None) -> bool:
        """Start playback of the current playlist."""
        return self.media_player.play(target)
        
    def pause(self, target: Union[str, List[str]] = None) -> bool:
        """Pause playback."""
        return self.media_player.pause(target)
        
    def resume(self, target: Union[str, List[str]] = None) -> bool:
        """Resume playback."""
        return self.media_player.resume(target)
        
    def stop(self, target: Union[str, List[str]] = None) -> bool:
        """Stop playback."""
        return self.media_player.stop(target)
        
    def next(self, target: Union[str, List[str]] = None) -> bool:
        """Play the next track."""
        result = self.media_player.next(target)
        # Update index reference
        self.current_index = self.media_player.current_index
        return result
        
    def previous(self, target: Union[str, List[str]] = None) -> bool:
        """Play the previous track."""
        result = self.media_player.previous(target)
        # Update index reference
        self.current_index = self.media_player.current_index
        return result
        
    # --- Media Extraction Methods ---
    
    def add_media(self, playlist_name: str, title: str, url: str) -> bool:
        """
        Add media to a playlist, with optional extraction from X/Twitter.
        
        Args:
            playlist_name: Name of the playlist
            title: Title of the media
            url: URL of the media or X/Twitter post
            
        Returns:
            True if successful, False otherwise
        """
        # This is a simplified version - in the real implementation,
        # we would check if the URL is from X/Twitter and extract the video URL
        return self.add_to_playlist(playlist_name, url, title)
