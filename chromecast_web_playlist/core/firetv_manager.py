#!/usr/bin/env python3
"""
Fire TV Device Manager Component
Handles Fire TV device discovery, connection, and control
"""

import os
import time
import logging
import socket
import yaml
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
import asyncio

# Fire TV dependencies
from firetv import FireTV

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FireTVManager:
    """
    Manage Fire TV devices.
    Handles device discovery, connection, and media control.
    """
    
    def __init__(self):
        """Initialize the FireTVManager."""
        # Device storage
        self.connected_devices = {}  # Dictionary of device_name: firetv_object
        self.device_statuses = {}    # Dictionary of device_name: status_dict
        
        # Configuration
        self.config_dir = os.path.join(str(Path.home()), ".castcomplete")
        self.devices_config = os.path.join(self.config_dir, "firetv_devices.yaml")
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Load saved devices
        self.saved_devices = self._load_saved_devices()
        
        # Maintain backward compatibility
        self.active_device = None    # Name of currently active device
    
    def _load_saved_devices(self) -> Dict[str, Dict]:
        """
        Load saved FireTV devices from configuration.
        
        Returns:
            Dictionary of device_name: device_info
        """
        if not os.path.exists(self.devices_config):
            return {}
            
        try:
            with open(self.devices_config, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading Fire TV devices: {e}")
            return {}
    
    def _save_devices(self):
        """Save Fire TV devices to configuration."""
        try:
            with open(self.devices_config, 'w') as f:
                yaml.dump(self.saved_devices, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error saving Fire TV devices: {e}")
    
    def discover_devices(self) -> List[str]:
        """
        Return list of saved FireTV devices.
        
        Returns:
            List of device names
        """
        return list(self.saved_devices.keys())
    
    def save_device(self, name: str, host: str, port: int = 5555) -> bool:
        """
        Save a new Fire TV device.
        
        Args:
            name: Friendly name of the device
            host: IP address of the device
            port: ADB port (default: 5555)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Basic validation
            if not name or not host:
                logger.error("Device name and host are required")
                return False
            
            # Test if device is reachable
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result != 0:
                    logger.error(f"Cannot reach Fire TV at {host}:{port}")
                    return False
            except Exception as e:
                logger.error(f"Error connecting to Fire TV at {host}:{port}: {e}")
                return False
            
            # Save device
            self.saved_devices[name] = {
                'host': host,
                'port': port
            }
            self._save_devices()
            
            logger.info(f"Saved Fire TV device: {name} at {host}:{port}")
            return True
        except Exception as e:
            logger.error(f"Error saving Fire TV device: {e}")
            return False
    
    def remove_device(self, name: str) -> bool:
        """
        Remove a saved Fire TV device.
        
        Args:
            name: Name of the device to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if name in self.saved_devices:
                # Disconnect if connected
                if name in self.connected_devices:
                    self.disconnect(name)
                
                # Remove from saved devices
                del self.saved_devices[name]
                self._save_devices()
                
                logger.info(f"Removed Fire TV device: {name}")
                return True
            else:
                logger.error(f"Device {name} not found")
                return False
        except Exception as e:
            logger.error(f"Error removing Fire TV device: {e}")
            return False
    
    def connect(self, device_name: str) -> bool:
        """
        Connect to a Fire TV device.
        
        Args:
            device_name: Name of the device to connect to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if device exists
            if device_name not in self.saved_devices:
                logger.error(f"Device {device_name} not found in saved devices")
                return False
                
            # Check if already connected
            if device_name in self.connected_devices:
                logger.info(f"Already connected to {device_name}")
                return True
                
            # Get device info
            device_info = self.saved_devices[device_name]
            host = device_info['host']
            port = device_info.get('port', 5555)
            
            # Create FireTV instance
            ftv = FireTV(host, port)
            
            # Test connection
            if not ftv.connect():
                logger.error(f"Failed to connect to Fire TV at {host}:{port}")
                return False
            
            # Store the device
            self.connected_devices[device_name] = ftv
            
            # Set as active device
            self.active_device = device_name
            
            # Initialize device status
            self.device_statuses[device_name] = {
                "playing": ftv.media_state.value == "PLAYING",
                "connected": True
            }
            
            logger.info(f"Connected to Fire TV: {device_name}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to Fire TV: {e}")
            return False
    
    def disconnect(self, device_name: str = None) -> bool:
        """
        Disconnect from a Fire TV device.
        
        Args:
            device_name: Name of the device to disconnect from, or None for all devices
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Disconnect all devices
            if device_name is None:
                for name, device in list(self.connected_devices.items()):
                    try:
                        device.disconnect()
                        del self.connected_devices[name]
                        if name in self.device_statuses:
                            del self.device_statuses[name]
                    except Exception as e:
                        logger.error(f"Error disconnecting from {name}: {e}")
                
                if self.active_device in self.connected_devices:
                    self.active_device = None
                
                logger.info("Disconnected from all Fire TV devices")
                return True
            
            # Disconnect specific device
            if device_name in self.connected_devices:
                try:
                    self.connected_devices[device_name].disconnect()
                    del self.connected_devices[device_name]
                    
                    if device_name in self.device_statuses:
                        del self.device_statuses[device_name]
                        
                    if self.active_device == device_name:
                        self.active_device = None
                        
                    logger.info(f"Disconnected from {device_name}")
                    return True
                except Exception as e:
                    logger.error(f"Error disconnecting from {device_name}: {e}")
                    return False
            else:
                logger.error(f"Not connected to {device_name}")
                return False
        except Exception as e:
            logger.error(f"Error in disconnect: {e}")
            return False
    
    def get_status(self, device_name: str = None) -> Dict:
        """
        Get the status of a Fire TV device.
        
        Args:
            device_name: Name of the device, or None for active device
            
        Returns:
            Device status dictionary
        """
        # Determine target device
        target = device_name if device_name else self.active_device
        
        if not target:
            logger.error("No target device specified and no active device")
            return {"error": "No target device"}
            
        if target not in self.connected_devices:
            logger.error(f"Not connected to {target}")
            return {"error": f"Not connected to {target}"}
            
        try:
            device = self.connected_devices[target]
            
            # Update status
            self.device_statuses[target] = {
                "playing": device.media_state.value == "PLAYING",
                "connected": device.available,
                "state": device.state.value
            }
            
            return self.device_statuses[target]
        except Exception as e:
            logger.error(f"Error getting status for {target}: {e}")
            return {"error": str(e)}
    
    # Media control methods
    def play(self, device_name: str = None) -> bool:
        """Start or resume playback."""
        target = device_name if device_name else self.active_device
        if not target or target not in self.connected_devices:
            return False
        
        try:
            return self.connected_devices[target].media_play()
        except Exception as e:
            logger.error(f"Error playing on {target}: {e}")
            return False
    
    def pause(self, device_name: str = None) -> bool:
        """Pause playback."""
        target = device_name if device_name else self.active_device
        if not target or target not in self.connected_devices:
            return False
        
        try:
            return self.connected_devices[target].media_pause()
        except Exception as e:
            logger.error(f"Error pausing on {target}: {e}")
            return False
    
    def resume(self, device_name: str = None) -> bool:
        """Resume playback (alias for play)."""
        return self.play(device_name)
    
    def stop(self, device_name: str = None) -> bool:
        """Stop playback."""
        target = device_name if device_name else self.active_device
        if not target or target not in self.connected_devices:
            return False
        
        try:
            return self.connected_devices[target].media_stop()
        except Exception as e:
            logger.error(f"Error stopping on {target}: {e}")
            return False
    
    def next(self, device_name: str = None) -> bool:
        """Play next track."""
        target = device_name if device_name else self.active_device
        if not target or target not in self.connected_devices:
            return False
        
        try:
            return self.connected_devices[target].media_next()
        except Exception as e:
            logger.error(f"Error skipping to next on {target}: {e}")
            return False
    
    def previous(self, device_name: str = None) -> bool:
        """Play previous track."""
        target = device_name if device_name else self.active_device
        if not target or target not in self.connected_devices:
            return False
        
        try:
            return self.connected_devices[target].media_previous()
        except Exception as e:
            logger.error(f"Error going to previous on {target}: {e}")
            return False
    
    def home(self, device_name: str = None) -> bool:
        """Press home button."""
        target = device_name if device_name else self.active_device
        if not target or target not in self.connected_devices:
            return False
        
        try:
            return self.connected_devices[target].home()
        except Exception as e:
            logger.error(f"Error pressing home on {target}: {e}")
            return False
    
    def launch_app(self, app_id: str, device_name: str = None) -> bool:
        """
        Launch an app on the device.
        
        Args:
            app_id: Application ID to launch
            device_name: Target device name
            
        Returns:
            True if successful, False otherwise
        """
        target = device_name if device_name else self.active_device
        if not target or target not in self.connected_devices:
            return False
        
        try:
            return self.connected_devices[target].launch_app(app_id)
        except Exception as e:
            logger.error(f"Error launching app {app_id} on {target}: {e}")
            return False
