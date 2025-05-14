#!/usr/bin/env python3
"""
Device Manager Component
Handles Chromecast device discovery, connection, and group management
"""

import json
import os
import time
from typing import Dict, List, Optional, Any, Tuple, Union

# External dependencies
import pychromecast
from pychromecast.controllers.media import MediaController
import zeroconf

class DeviceManager:
    """
    Manage Chromecast devices and device groups.
    Handles device discovery, connection, and group management.
    Also supports web clients as devices.
    """
    
    def __init__(self):
        """Initialize the DeviceManager."""
        # Multi-device support
        self.connected_devices = {}  # Dictionary of device_name: chromecast_object
        self.media_controllers = {}  # Dictionary of device_name: media_controller
        self.device_statuses = {}    # Dictionary of device_name: status_dict
        self.device_groups = {}      # Dictionary of group_name: list_of_device_names
        
        # Web client support
        self.web_clients = {}        # Dictionary of client_id: client_info
        self.all_devices = {}        # Combined dictionary of all devices (Chromecasts and web clients)
        
        # Maintain backward compatibility
        self.chromecast = None       # Currently active device
        self.media_controller = None # Media controller for active device
        self.active_device = None    # Name of currently active device
        
        self.zeroconf = None
        
        # Configuration
        self.sync_tolerance = 0.5    # Seconds of tolerance for sync
        self.sync_interval = 10      # Seconds between sync checks
        
    def discover_devices(self) -> List[str]:
        """
        Discover available Chromecast devices on the network.
        
        Returns:
            List of device names
        """
        try:
            # Initialize zeroconf if needed
            if not self.zeroconf:
                self.zeroconf = zeroconf.Zeroconf()
                
            # First, discover services
            print("Discovering Chromecast services...")
            services, browser = pychromecast.discovery.discover_chromecasts(
                zeroconf_instance=self.zeroconf)
            
            # Give it time to discover all devices
            time.sleep(3)
            
            # Get the discovered devices
            print("Getting discovered Chromecasts...")
            chromecasts, browser = pychromecast.get_listed_chromecasts(
                friendly_names=None, 
                uuids=None, 
                discovery_timeout=20,  # Increased timeout for better discovery
                zeroconf_instance=self.zeroconf)
            
            # Extract device names
            devices = [cast.device.friendly_name for cast in chromecasts]
            print(f"Discovered {len(devices)} Chromecast devices: {devices}")
            
            # Add any web clients
            web_client_names = [client['name'] for client in self.web_clients.values()]
            print(f"Found {len(web_client_names)} web clients: {web_client_names}")
            
            # Combine all devices
            all_devices = devices + web_client_names
            print(f"Total devices: {len(all_devices)} (Chromecasts: {len(devices)}, Web clients: {len(web_client_names)})")
            
            # Make sure all web clients have device statuses
            for client_id, client_info in self.web_clients.items():
                device_name = client_info['name']
                if device_name not in self.device_statuses:
                    self.device_statuses[device_name] = {
                        'status': 'connected',
                        'player_state': 'IDLE',
                        'content_id': None,
                        'content_type': None,
                        'duration': 0,
                        'current_time': 0,
                        'volume_level': 1.0,
                        'is_muted': False,
                        'playing': False
                    }
            
            return all_devices
        except Exception as e:
            print(f"Error discovering devices: {e}")
            import traceback
            traceback.print_exc()
            return []
            
    def connect(self, device_name: str) -> bool:
        """
        Connect to a Chromecast device.
        
        Args:
            device_name: Name of the device to connect to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if already connected
            if device_name in self.connected_devices:
                print(f"Already connected to {device_name}")
                return True
                
            # Initialize zeroconf if needed
            if not self.zeroconf:
                self.zeroconf = zeroconf.Zeroconf()
                
            # Get list of chromecasts
            chromecasts = pychromecast.get_listed_chromecasts(friendly_names=[device_name], 
                                                              zeroconf_instance=self.zeroconf)
            
            if not chromecasts[0]:
                print(f"Device {device_name} not found")
                return False
                
            cast = chromecasts[0][0]
            cast.wait()
            
            # Store the device
            self.connected_devices[device_name] = cast
            self.media_controllers[device_name] = cast.media_controller
            
            # Set as active device for backward compatibility
            self.chromecast = cast
            self.media_controller = cast.media_controller
            self.active_device = device_name
            
            # Initialize device status
            self.device_statuses[device_name] = {
                "playing": False,
                "current_playlist": None,
                "current_index": 0,
                "current_item": None,
                "position": 0
            }
            
            print(f"Connected to {device_name}")
            return True
        except Exception as e:
            print(f"Error connecting to {device_name}: {e}")
            return False
            
    def disconnect(self, device_name: str = None) -> bool:
        """
        Disconnect from a Chromecast device.
        
        Args:
            device_name: Name of the device to disconnect from, or None for all devices
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if device_name:
                # Disconnect specific device
                if device_name not in self.connected_devices:
                    print(f"Not connected to {device_name}")
                    return False
                    
                cast = self.connected_devices[device_name]
                cast.disconnect()
                
                del self.connected_devices[device_name]
                del self.media_controllers[device_name]
                del self.device_statuses[device_name]
                
                # Update active device if needed
                if self.active_device == device_name:
                    self.chromecast = None
                    self.media_controller = None
                    self.active_device = None
                    
                    # Set a new active device if available
                    if self.connected_devices:
                        new_device = list(self.connected_devices.keys())[0]
                        self.chromecast = self.connected_devices[new_device]
                        self.media_controller = self.media_controllers[new_device]
                        self.active_device = new_device
            else:
                # Disconnect all devices
                for name, cast in self.connected_devices.items():
                    cast.disconnect()
                    
                self.connected_devices = {}
                self.media_controllers = {}
                self.device_statuses = {}
                
                self.chromecast = None
                self.media_controller = None
                self.active_device = None
                
            return True
        except Exception as e:
            print(f"Error disconnecting: {e}")
            return False
            
    def get_device_groups(self) -> Dict[str, List[str]]:
        """
        Get all device groups.
        
        Returns:
            Dictionary of group_name: list_of_device_names
        """
        return self.device_groups
        
    def create_device_group(self, name: str, device_names: List[str] = None) -> bool:
        """
        Create a new device group.
        
        Args:
            name: Name of the group
            device_names: List of device names to add to the group
            
        Returns:
            True if successful, False otherwise
        """
        if name in self.device_groups:
            print(f"Group {name} already exists")
            return False
            
        if device_names is None:
            device_names = []
            
        # Validate device names
        valid_devices = []
        for device in device_names:
            if device in self.connected_devices:
                valid_devices.append(device)
            else:
                print(f"Device {device} not connected, skipping")
                
        self.device_groups[name] = valid_devices
        return True
        
    def delete_device_group(self, name: str) -> bool:
        """
        Delete a device group.
        
        Args:
            name: Name of the group
            
        Returns:
            True if successful, False otherwise
        """
        if name not in self.device_groups:
            print(f"Group {name} does not exist")
            return False
            
        del self.device_groups[name]
        return True
        
    def add_to_device_group(self, group_name: str, device_name: str) -> bool:
        """
        Add a device to a group.
        
        Args:
            group_name: Name of the group
            device_name: Name of the device to add
            
        Returns:
            True if successful, False otherwise
        """
        # Log the request for debugging
        print(f"Adding device '{device_name}' to group '{group_name}'")
        
        # Check if group exists
        if group_name not in self.device_groups:
            print(f"Group {group_name} does not exist")
            return False
        
        # Check if device is already in the group
        if device_name in self.device_groups[group_name]:
            print(f"Device {device_name} already in group {group_name}")
            return True
        
        # Check if device exists in all_devices (includes both Chromecasts and web clients)
        device_exists = False
        
        # Check in connected Chromecast devices
        if device_name in self.connected_devices:
            device_exists = True
            print(f"Found device {device_name} in connected Chromecast devices")
        
        # Check in web clients
        for client_id, client_info in self.web_clients.items():
            if client_info['name'] == device_name:
                device_exists = True
                print(f"Found device {device_name} in web clients (ID: {client_id})")
                break
        
        # Check in all_devices as a fallback
        if device_name in self.all_devices:
            device_exists = True
            print(f"Found device {device_name} in all_devices dictionary")
        
        if not device_exists:
            print(f"Device {device_name} not found in any device list")
            return False
        
        # Add device to group
        self.device_groups[group_name].append(device_name)
        print(f"Successfully added {device_name} to group {group_name}")
        return True
        
    def remove_from_device_group(self, group_name: str, device_name: str) -> bool:
        """
        Remove a device from a group.
        
        Args:
            group_name: Name of the group
            device_name: Name of the device to remove
            
        Returns:
            True if successful, False otherwise
        """
        if group_name not in self.device_groups:
            print(f"Group {group_name} does not exist")
            return False
            
        if device_name not in self.device_groups[group_name]:
            print(f"Device {device_name} not in group {group_name}")
            return False
            
        self.device_groups[group_name].remove(device_name)
        return True
    
    # --- Web Client Management Methods ---
    
    def register_web_client(self, client_id: str, client_info: Dict[str, Any]) -> bool:
        """
        Register a web client as a device.
        
        Args:
            client_id: Unique identifier for the client
            client_info: Information about the client (name, type, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate a friendly name if not provided
            if 'name' not in client_info or not client_info['name']:
                client_info['name'] = f"Web Client {client_id[:8]}"
                
            # Add type information
            client_info['type'] = 'web_client'
            client_info['connected'] = True
            client_info['last_seen'] = time.time()
            
            # Register the client
            self.web_clients[client_id] = client_info
            
            # Add to all devices
            device_name = client_info['name']
            self.all_devices[device_name] = {
                'id': client_id,
                'type': 'web_client',
                'info': client_info
            }
            
            # Update device status
            self.device_statuses[device_name] = {
                'status': 'connected',
                'player_state': 'IDLE',
                'content_id': None,
                'content_type': None,
                'duration': 0,
                'current_time': 0,
                'volume_level': 1.0,
                'is_muted': False,
                'playing': False
            }
            
            print(f"Registered web client: {device_name} ({client_id})")
            return True
        except Exception as e:
            print(f"Error registering web client: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def update_web_client(self, client_id: str, status_update: Dict[str, Any]) -> bool:
        """
        Update the status of a web client.
        
        Args:
            client_id: Client ID
            status_update: Status update information
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if client_id not in self.web_clients:
                return False
                
            # Update last seen timestamp
            self.web_clients[client_id]['last_seen'] = time.time()
            
            # Update client info with new status
            self.web_clients[client_id].update(status_update)
            
            # Update device status if needed
            device_name = self.web_clients[client_id]['name']
            if 'player_state' in status_update:
                self.device_statuses[device_name]['player_state'] = status_update['player_state']
            if 'current_time' in status_update:
                self.device_statuses[device_name]['current_time'] = status_update['current_time']
            if 'volume_level' in status_update:
                self.device_statuses[device_name]['volume_level'] = status_update['volume_level']
            
            return True
        except Exception as e:
            print(f"Error updating web client: {e}")
            return False
    
    def remove_web_client(self, client_id: str) -> bool:
        """
        Remove a web client.
        
        Args:
            client_id: Client ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Log the current state for debugging
            print(f"Removing web client {client_id}")
            print(f"Current web clients: {self.web_clients}")
            
            # Check if client exists
            if client_id not in self.web_clients:
                print(f"Web client {client_id} not found in registered clients")
                # Return True anyway to allow client-side cleanup
                return True
                
            # Get device name
            device_name = self.web_clients[client_id]['name']
            print(f"Found device name: {device_name}")
            
            # Remove from web clients
            del self.web_clients[client_id]
            print(f"Removed from web_clients dictionary")
            
            # Remove from all devices
            if device_name in self.all_devices:
                del self.all_devices[device_name]
                print(f"Removed from all_devices dictionary")
            else:
                print(f"Device {device_name} not found in all_devices")
                
            # Remove from device statuses
            if device_name in self.device_statuses:
                del self.device_statuses[device_name]
                print(f"Removed from device_statuses dictionary")
            else:
                print(f"Device {device_name} not found in device_statuses")
                
            # Remove from any groups
            for group_name, devices in list(self.device_groups.items()):
                if device_name in devices:
                    self.device_groups[group_name].remove(device_name)
                    print(f"Removed from group {group_name}")
            
            print(f"Successfully removed web client: {device_name} ({client_id})")
            return True
        except Exception as e:
            import traceback
            print(f"Error removing web client: {e}")
            print(traceback.format_exc())
            # Return True anyway to allow client-side cleanup
            return True
    
    def get_all_devices(self) -> List[str]:
        """
        Get all connected devices (Chromecasts, web clients, and groups).
        
        Returns:
            List of device names
        """
        chromecast_devices = list(self.connected_devices.keys())
        web_clients = [client['name'] for client in self.web_clients.values()]
        groups = list(self.device_groups.keys())
        return chromecast_devices + web_clients + groups
        
    def sync_device_group(self, group_name: str) -> bool:
        """
        Synchronize playback across devices in a group.
        
{{ ... }}
            group_name: Name of the group
            
        Returns:
            True if successful, False otherwise
        """
        if group_name not in self.device_groups:
            print(f"Group {group_name} does not exist")
            return False
            
        device_names = self.device_groups[group_name]
        if not device_names:
            print(f"Group {group_name} has no devices")
            return False
            
        # Get reference device (first device in group)
        reference_device = device_names[0]
        if reference_device not in self.connected_devices:
            print(f"Reference device {reference_device} not connected")
            return False
            
        # Get reference status
        ref_status = self.device_statuses[reference_device]
        if not ref_status["playing"]:
            print(f"Reference device {reference_device} not playing")
            return False
            
        # Sync other devices to reference
        for device in device_names[1:]:
            if device not in self.connected_devices:
                print(f"Device {device} not connected, skipping")
                continue
                
            # TODO: Implement actual synchronization logic
            # This would involve pausing all devices, seeking to the same position,
            # and then resuming playback simultaneously
                
        return True
