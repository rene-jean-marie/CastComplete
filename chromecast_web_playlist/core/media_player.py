#!/usr/bin/env python3
"""
Media Player Component
Handles playback functionality for Chromecast devices
"""

import time
from typing import Dict, List, Optional, Any, Tuple, Union

from .playlist_manager import PlaylistManager
from .device_manager import DeviceManager

class MediaPlayer:
    """
    Media playback functionality for Chromecast devices.
    Handles playback control across individual devices or groups.
    """
    
    def __init__(self, playlist_manager: PlaylistManager, device_manager: DeviceManager):
        """
        Initialize the MediaPlayer.
        
        Args:
            playlist_manager: PlaylistManager instance
            device_manager: DeviceManager instance
        """
        self.playlist_manager = playlist_manager
        self.device_manager = device_manager
        
        self.current_playlist = None
        self.current_index = 0
        
    def load_playlist(self, playlist_name: str, target: Union[str, List[str]] = None) -> bool:
        """
        Load a playlist for playback.
        
        Args:
            playlist_name: Name of the playlist to load
            target: Target device or group name, or list of device names
            
        Returns:
            True if successful, False otherwise
        """
        # Validate playlist
        playlist = self.playlist_manager.get_playlist(playlist_name)
        if not playlist:
            print(f"Playlist '{playlist_name}' not found")
            return False
            
        # Resolve target devices
        devices = self._resolve_target(target)
        if not devices:
            print("No valid target devices")
            return False
            
        # Set current playlist
        self.current_playlist = playlist_name
        self.current_index = 0
        
        # Update device statuses
        for device in devices:
            self.device_manager.device_statuses[device]["current_playlist"] = playlist_name
            self.device_manager.device_statuses[device]["current_index"] = 0
            
            if playlist:
                self.device_manager.device_statuses[device]["current_item"] = playlist[0]
            else:
                self.device_manager.device_statuses[device]["current_item"] = None
                
        return True
        
    def play(self, target: Union[str, List[str]] = None) -> bool:
        """
        Start playback of the current playlist.
        
        Args:
            target: Target device or group name, or list of device names
            
        Returns:
            True if successful, False otherwise
        """
        # Resolve target devices
        devices = self._resolve_target(target)
        if not devices:
            print("No valid target devices")
            return False
            
        # Check if playlist is loaded
        if not self.current_playlist:
            print("No playlist loaded")
            return False
            
        playlist = self.playlist_manager.get_playlist(self.current_playlist)
        if not playlist:
            print(f"Playlist '{self.current_playlist}' not found")
            return False
            
        # Check if index is valid
        if self.current_index >= len(playlist):
            print(f"Invalid index {self.current_index} for playlist '{self.current_playlist}'")
            return False
            
        # Get current item
        item = playlist[self.current_index]
        
        # Play on all target devices
        success = False
        for device in devices:
            if device not in self.device_manager.connected_devices:
                print(f"Device {device} not connected, skipping")
                continue
                
            try:
                cast = self.device_manager.connected_devices[device]
                mc = self.device_manager.media_controllers[device]
                
                # Play the media
                mc.play_media(item["url"], "video/mp4", title=item["title"])
                mc.block_until_active()
                
                # Update device status
                self.device_manager.device_statuses[device]["playing"] = True
                self.device_manager.device_statuses[device]["current_playlist"] = self.current_playlist
                self.device_manager.device_statuses[device]["current_index"] = self.current_index
                self.device_manager.device_statuses[device]["current_item"] = item
                
                success = True
            except Exception as e:
                print(f"Error playing on device {device}: {e}")
                
        return success
        
    def pause(self, target: Union[str, List[str]] = None) -> bool:
        """
        Pause playback.
        
        Args:
            target: Target device or group name, or list of device names
            
        Returns:
            True if successful, False otherwise
        """
        # Resolve target devices
        devices = self._resolve_target(target)
        if not devices:
            print("No valid target devices")
            return False
            
        # Pause on all target devices
        success = False
        for device in devices:
            if device not in self.device_manager.connected_devices:
                print(f"Device {device} not connected, skipping")
                continue
                
            try:
                mc = self.device_manager.media_controllers[device]
                mc.pause()
                
                # Update device status
                self.device_manager.device_statuses[device]["playing"] = False
                
                success = True
            except Exception as e:
                print(f"Error pausing on device {device}: {e}")
                
        return success
        
    def resume(self, target: Union[str, List[str]] = None) -> bool:
        """
        Resume playback.
        
        Args:
            target: Target device or group name, or list of device names
            
        Returns:
            True if successful, False otherwise
        """
        # Resolve target devices
        devices = self._resolve_target(target)
        if not devices:
            print("No valid target devices")
            return False
            
        # Resume on all target devices
        success = False
        for device in devices:
            if device not in self.device_manager.connected_devices:
                print(f"Device {device} not connected, skipping")
                continue
                
            try:
                mc = self.device_manager.media_controllers[device]
                mc.play()
                
                # Update device status
                self.device_manager.device_statuses[device]["playing"] = True
                
                success = True
            except Exception as e:
                print(f"Error resuming on device {device}: {e}")
                
        return success
        
    def stop(self, target: Union[str, List[str]] = None) -> bool:
        """
        Stop playback.
        
        Args:
            target: Target device or group name, or list of device names
            
        Returns:
            True if successful, False otherwise
        """
        # Resolve target devices
        devices = self._resolve_target(target)
        if not devices:
            print("No valid target devices")
            return False
            
        # Stop on all target devices
        success = False
        for device in devices:
            if device not in self.device_manager.connected_devices:
                print(f"Device {device} not connected, skipping")
                continue
                
            try:
                mc = self.device_manager.media_controllers[device]
                mc.stop()
                
                # Update device status
                self.device_manager.device_statuses[device]["playing"] = False
                
                success = True
            except Exception as e:
                print(f"Error stopping on device {device}: {e}")
                
        return success
        
    def next(self, target: Union[str, List[str]] = None) -> bool:
        """
        Play the next track.
        
        Args:
            target: Target device or group name, or list of device names
            
        Returns:
            True if successful, False otherwise
        """
        # Check if playlist is loaded
        if not self.current_playlist:
            print("No playlist loaded")
            return False
            
        playlist = self.playlist_manager.get_playlist(self.current_playlist)
        if not playlist:
            print(f"Playlist '{self.current_playlist}' not found")
            return False
            
        # Increment index
        self.current_index += 1
        
        # Loop back to start if at end
        if self.current_index >= len(playlist):
            self.current_index = 0
            
        # Play the next track
        return self.play(target)
        
    def previous(self, target: Union[str, List[str]] = None) -> bool:
        """
        Play the previous track.
        
        Args:
            target: Target device or group name, or list of device names
            
        Returns:
            True if successful, False otherwise
        """
        # Check if playlist is loaded
        if not self.current_playlist:
            print("No playlist loaded")
            return False
            
        playlist = self.playlist_manager.get_playlist(self.current_playlist)
        if not playlist:
            print(f"Playlist '{self.current_playlist}' not found")
            return False
            
        # Decrement index
        self.current_index -= 1
        
        # Loop to end if at start
        if self.current_index < 0:
            self.current_index = len(playlist) - 1
            
        # Play the previous track
        return self.play(target)
        
    def _resolve_target(self, target: Union[str, List[str]] = None) -> List[str]:
        """
        Resolve a target (device or group name) to a list of device names.
        
        Args:
            target: Target device or group name, or list of device names
            
        Returns:
            List of device names
        """
        if not target:
            # Default to active device if available
            if self.device_manager.active_device:
                return [self.device_manager.active_device]
            # Otherwise, use all connected devices
            return list(self.device_manager.connected_devices.keys())
            
        if isinstance(target, list):
            # Target is already a list of device names
            return [device for device in target if device in self.device_manager.connected_devices]
            
        # Check if target is a group
        if target in self.device_manager.device_groups:
            return [device for device in self.device_manager.device_groups[target] 
                    if device in self.device_manager.connected_devices]
                    
        # Check if target is a device
        if target in self.device_manager.connected_devices:
            return [target]
            
        # Invalid target
        return []
