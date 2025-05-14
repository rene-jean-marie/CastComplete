#!/usr/bin/env python3
"""
API Routes
Flask API routes for the Chromecast Web Playlist Manager
"""

import os
import json
import time
import logging
import urllib.parse
import requests
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, render_template, request, jsonify, send_from_directory, Response
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_api_routes(app, chromecast_manager, playback_status, 
                       static_dir, templates_dir, downloads_dir, media_dir):
    """
    Register API routes for the Flask app.
    
    Args:
        app: Flask app
        chromecast_manager: ChromecastManager instance
        playback_status: Playback status dictionary
        static_dir: Path to static files
        templates_dir: Path to templates
        downloads_dir: Path to downloads directory
        media_dir: Path to media directory
    """
    
    # Helper function to resolve target
    def resolve_target(target):
        """Resolve a target (device or group name) to a list of device names."""
        if not target:
            # Default to all connected devices
            return list(chromecast_manager.get_all_devices())
        if target in chromecast_manager.device_groups:
            return chromecast_manager.device_groups[target]
        elif target in chromecast_manager.connected_devices:
            return [target]
        elif any(client['name'] == target for client in chromecast_manager.web_clients.values()):
            return [target]
        else:
            return []
    
    # --- Device Management Routes ---
    
    @app.route('/api/devices', methods=['GET'])
    def get_devices():
        """Get available Chromecast devices"""
        try:
            devices = chromecast_manager.discover_devices()
            return jsonify({"success": True, "devices": devices})
        except Exception as e:
            logger.error(f"Error discovering devices: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/connect', methods=['POST'])
    def connect_device():
        """Connect to a Chromecast device"""
        try:
            data = request.get_json(force=True)
            device = data.get('device')
            
            if not device:
                return jsonify({"success": False, "error": "Device name is required"})
                
            success = chromecast_manager.connect(device)
            
            if success:
                playback_status["active_device"] = device
                playback_status["connected_devices"] = chromecast_manager.device_statuses
                
                # Emit status update via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('status_update', playback_status)
                    
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": f"Failed to connect to {device}"})
        except Exception as e:
            logger.error(f"Error connecting to device: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/disconnect', methods=['POST'])
    def disconnect_device():
        """Disconnect from a Chromecast device"""
        try:
            data = request.get_json(force=True) if request.is_json else {}
            device = data.get('device')
            
            success = chromecast_manager.disconnect(device)
            
            if success:
                if device:
                    if device == playback_status["active_device"]:
                        playback_status["active_device"] = None
                    if device in playback_status["connected_devices"]:
                        del playback_status["connected_devices"][device]
                else:
                    playback_status["active_device"] = None
                    playback_status["connected_devices"] = {}
                    
                # Emit status update via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('status_update', playback_status)
                    
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": "Failed to disconnect"})
        except Exception as e:
            logger.error(f"Error disconnecting from device: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    # --- Device Group Management Routes ---
    
    @app.route('/api/groups', methods=['GET'])
    def get_device_groups():
        """Get all device groups"""
        try:
            groups = chromecast_manager.get_device_groups()
            return jsonify({"success": True, "groups": groups})
        except Exception as e:
            logger.error(f"Error getting device groups: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/groups', methods=['POST'])
    def create_device_group():
        """Create a new device group"""
        try:
            data = request.get_json(force=True)
            name = data.get('name')
            device_names = data.get('devices', [])
            
            if not name:
                return jsonify({"success": False, "error": "Group name is required"})
                
            success = chromecast_manager.create_device_group(name, device_names)
            
            if success:
                playback_status["device_groups"] = chromecast_manager.get_device_groups()
                
                # Emit status update via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('status_update', playback_status)
                    
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": f"Failed to create group {name}"})
        except Exception as e:
            logger.error(f"Error creating device group: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/groups/<name>', methods=['DELETE'])
    def delete_device_group(name):
        """Delete a device group"""
        try:
            success = chromecast_manager.delete_device_group(name)
            
            if success:
                playback_status["device_groups"] = chromecast_manager.get_device_groups()
                
                if playback_status["active_group"] == name:
                    playback_status["active_group"] = None
                    
                # Emit status update via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('status_update', playback_status)
                    
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": f"Failed to delete group {name}"})
        except Exception as e:
            logger.error(f"Error deleting device group: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/groups/<name>/add', methods=['POST'])
    def add_to_device_group(name):
        """Add a device to a group"""
        try:
            data = request.get_json(force=True)
            device = data.get('device')
            
            if not device:
                return jsonify({"success": False, "error": "Device name is required"})
                
            success = chromecast_manager.add_to_device_group(name, device)
            
            if success:
                playback_status["device_groups"] = chromecast_manager.get_device_groups()
                
                # Emit status update via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('status_update', playback_status)
                    
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": f"Failed to add {device} to group {name}"})
        except Exception as e:
            logger.error(f"Error adding to device group: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/groups/<name>/remove', methods=['POST'])
    def remove_from_group(name):
        """Remove a device from a group"""
        try:
            data = request.get_json(force=True)
            device = data.get('device')
            
            if not device:
                return jsonify({"success": False, "error": "Device name is required"})
                
            success = chromecast_manager.remove_from_device_group(name, device)
            
            if success:
                playback_status["device_groups"] = chromecast_manager.get_device_groups()
                
                # Emit status update via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('status_update', playback_status)
                    
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": f"Failed to remove {device} from group {name}"})
        except Exception as e:
            logger.error(f"Error removing device from group: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
            
    # --- Web Client Management Routes ---
    
    @app.route('/api/web-clients/register', methods=['POST'])
    def register_web_client():
        """Register a web client as a device"""
        try:
            data = request.get_json(force=True)
            client_id = data.get('client_id')
            client_info = data.get('client_info', {})
            
            if not client_id:
                # Generate a client ID if not provided
                client_id = f"web_{int(time.time())}_{os.urandom(4).hex()}"
                
            # Set client name if not provided
            if 'name' not in client_info or not client_info['name']:
                # Use user agent or IP to create a meaningful name
                user_agent = request.headers.get('User-Agent', '')
                ip = request.remote_addr
                
                if 'Mobile' in user_agent:
                    device_type = 'Mobile'
                elif 'Tablet' in user_agent:
                    device_type = 'Tablet'
                else:
                    device_type = 'Desktop'
                    
                client_info['name'] = f"{device_type} {ip.split('.')[-1]}"
                
            success = chromecast_manager.register_web_client(client_id, client_info)
            
            if success:
                # Update playback status
                playback_status["connected_devices"] = chromecast_manager.device_statuses
                playback_status["web_clients"] = {
                    client_id: client_info['name'] for client_id, client_info in 
                    chromecast_manager.web_clients.items()
                }
                
                # Emit status update via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('status_update', playback_status)
                    
                return jsonify({
                    "success": True, 
                    "client_id": client_id,
                    "name": client_info['name']
                })
            else:
                return jsonify({"success": False, "error": "Failed to register web client"})
        except Exception as e:
            logger.error(f"Error registering web client: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/web-clients/update', methods=['POST'])
    def update_web_client():
        """Update web client status"""
        try:
            data = request.get_json(force=True)
            client_id = data.get('client_id')
            status_update = data.get('status', {})
            
            if not client_id:
                return jsonify({"success": False, "error": "Client ID is required"})
                
            success = chromecast_manager.update_web_client(client_id, status_update)
            
            if success:
                # Update playback status
                playback_status["connected_devices"] = chromecast_manager.device_statuses
                
                # Emit status update via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('status_update', playback_status)
                    
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": "Web client not found"})
        except Exception as e:
            logger.error(f"Error updating web client: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/web-clients/unregister', methods=['POST'])
    def unregister_web_client():
        """Unregister a web client"""
        try:
            data = request.get_json(force=True)
            client_id = data.get('client_id')
            
            if not client_id:
                return jsonify({"success": False, "error": "Client ID is required"})
                
            success = chromecast_manager.remove_web_client(client_id)
            
            if success:
                # Update playback status
                playback_status["connected_devices"] = chromecast_manager.device_statuses
                playback_status["web_clients"] = {
                    client_id: client_info['name'] for client_id, client_info in 
                    chromecast_manager.web_clients.items()
                }
                
                # Emit status update via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('status_update', playback_status)
                    
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": "Web client not found"})
        except Exception as e:
            logger.error(f"Error unregistering web client: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/groups/active', methods=['POST'])
    def set_active_group():
        """Set the active device group"""
        try:
            data = request.get_json(force=True)
            group_name = data.get('group')
            
            if not group_name:
                playback_status["active_group"] = None
                
                # Emit status update via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('status_update', playback_status)
                    
                return jsonify({"success": True})
                
            if group_name not in chromecast_manager.device_groups:
                return jsonify({"success": False, "error": f"Group {group_name} does not exist"})
                
            playback_status["active_group"] = group_name
            
            # Emit status update via Socket.IO
            if hasattr(app, 'socketio'):
                app.socketio.emit('status_update', playback_status)
                
            return jsonify({"success": True})
        except Exception as e:
            logger.error(f"Error setting active group: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/groups/<name>/sync', methods=['POST'])
    def sync_device_group(name):
        """Synchronize playback across devices in a group"""
        try:
            success = chromecast_manager.sync_device_group(name)
            
            if success:
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": f"Failed to sync group {name}"})
        except Exception as e:
            logger.error(f"Error syncing device group: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    # --- Playlist Management Routes ---
    
    @app.route('/api/playlists', methods=['GET'])
    def get_playlists():
        """Get all playlists"""
        try:
            playlists = chromecast_manager.get_playlists()
            return jsonify({"success": True, "playlists": playlists})
        except Exception as e:
            logger.error(f"Error getting playlists: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/playlist/<name>', methods=['GET'])
    def get_playlist(name):
        """Get contents of a specific playlist"""
        try:
            playlist = chromecast_manager.get_playlist(name)
            return jsonify({"success": True, "playlist": playlist})
        except Exception as e:
            logger.error(f"Error getting playlist {name}: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/playlist', methods=['POST'])
    def create_playlist():
        """Create a new playlist"""
        try:
            data = request.get_json(force=True)
            name = data.get('name')
            
            if not name:
                return jsonify({"success": False, "error": "Playlist name is required"})
                
            success = chromecast_manager.create_playlist(name)
            
            if success:
                # Emit playlists updated via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('playlists_updated')
                    
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": f"Failed to create playlist {name}"})
        except Exception as e:
            logger.error(f"Error creating playlist: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/playlist/<name>', methods=['DELETE'])
    def delete_playlist(name):
        """Delete a playlist"""
        try:
            success = chromecast_manager.delete_playlist(name)
            
            if success:
                # Emit playlists updated via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('playlists_updated')
                    
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": f"Failed to delete playlist {name}"})
        except Exception as e:
            logger.error(f"Error deleting playlist: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/playlist/<name>/add', methods=['POST'])
    def add_to_playlist(name):
        """Add media to a playlist"""
        try:
            data = request.get_json(force=True)
            url = data.get('url')
            title = data.get('title')
            
            if not url:
                return jsonify({"success": False, "error": "URL is required"})
                
            success = chromecast_manager.add_to_playlist(name, url, title)
            
            if success:
                # Emit playlist content updated via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('playlist_content_updated', {"playlist": name})
                    
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": f"Failed to add to playlist {name}"})
        except Exception as e:
            logger.error(f"Error adding to playlist: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/playlist/<name>/remove/<int:index>', methods=['DELETE'])
    def remove_from_playlist(name, index):
        """Remove an item from a playlist"""
        try:
            success = chromecast_manager.remove_from_playlist(name, index)
            
            if success:
                # Emit playlist content updated via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('playlist_content_updated', {"playlist": name})
                    
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": f"Failed to remove from playlist {name}"})
        except Exception as e:
            logger.error(f"Error removing from playlist: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    # --- Playback Control Routes ---
    
    @app.route('/api/play', methods=['POST'])
    def play_playlist():
        """Play the current playlist on target devices or group"""
        try:
            data = request.get_json(force=True) if request.is_json else {}
            playlist_name = data.get('playlist')
            target = data.get('target')
            
            device_names = resolve_target(target)
            if not device_names:
                return jsonify({"success": False, "error": "No valid devices found for target"})
                
            # Load the playlist if specified
            if playlist_name:
                chromecast_manager.load_playlist(playlist_name, device_names)
                
            # Play the playlist
            success = chromecast_manager.play(device_names)
            
            if success:
                playback_status["playing"] = True
                playback_status["current_playlist"] = chromecast_manager.current_playlist
                playback_status["current_index"] = chromecast_manager.current_index
                playback_status["connected_devices"] = chromecast_manager.device_statuses
                
                # Get current item
                if chromecast_manager.current_playlist:
                    playlist = chromecast_manager.get_playlist(chromecast_manager.current_playlist)
                    if playlist and chromecast_manager.current_index < len(playlist):
                        playback_status["current_item"] = playlist[chromecast_manager.current_index]
                        
                # Emit status update via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('status_update', playback_status)
                    
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": "Failed to play playlist"})
        except Exception as e:
            logger.error(f"Error in play_playlist: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/pause', methods=['POST'])
    def pause_playback():
        """Pause playback on target devices or group"""
        try:
            data = request.get_json(force=True) if request.is_json else {}
            target = data.get('target')
            
            device_names = resolve_target(target)
            if not device_names:
                return jsonify({"success": False, "error": "No valid devices found for target"})
                
            success = chromecast_manager.pause(device_names)
            
            if success:
                playback_status["playing"] = False
                playback_status["connected_devices"] = chromecast_manager.device_statuses
                
                # Emit status update via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('status_update', playback_status)
                    
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": "Failed to pause playback"})
        except Exception as e:
            logger.error(f"Error in pause_playback: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/resume', methods=['POST'])
    def resume_playback():
        """Resume playback on target devices or group"""
        try:
            data = request.get_json(force=True) if request.is_json else {}
            target = data.get('target')
            
            device_names = resolve_target(target)
            if not device_names:
                return jsonify({"success": False, "error": "No valid devices found for target"})
                
            success = chromecast_manager.resume(device_names)
            
            if success:
                playback_status["playing"] = True
                playback_status["connected_devices"] = chromecast_manager.device_statuses
                
                # Emit status update via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('status_update', playback_status)
                    
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": "Failed to resume playback"})
        except Exception as e:
            logger.error(f"Error in resume_playback: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/next', methods=['POST'])
    def next_track():
        """Play the next track on target devices or group"""
        try:
            data = request.get_json(force=True) if request.is_json else {}
            target = data.get('target')
            
            device_names = resolve_target(target)
            if not device_names:
                return jsonify({"success": False, "error": "No valid devices found for target"})
                
            success = chromecast_manager.next(device_names)
            
            if success:
                playback_status["current_index"] = chromecast_manager.current_index
                playback_status["connected_devices"] = chromecast_manager.device_statuses
                
                # Get current item
                if chromecast_manager.current_playlist:
                    playlist = chromecast_manager.get_playlist(chromecast_manager.current_playlist)
                    if playlist and chromecast_manager.current_index < len(playlist):
                        playback_status["current_item"] = playlist[chromecast_manager.current_index]
                        
                # Emit status update via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('status_update', playback_status)
                    
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": "Failed to play next track"})
        except Exception as e:
            logger.error(f"Error in next_track: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/previous', methods=['POST'])
    def previous_track():
        """Play the previous track on target devices or group"""
        try:
            data = request.get_json(force=True) if request.is_json else {}
            target = data.get('target')
            
            device_names = resolve_target(target)
            if not device_names:
                return jsonify({"success": False, "error": "No valid devices found for target"})
                
            success = chromecast_manager.previous(device_names)
            
            if success:
                playback_status["current_index"] = chromecast_manager.current_index
                playback_status["connected_devices"] = chromecast_manager.device_statuses
                
                # Get current item
                if chromecast_manager.current_playlist:
                    playlist = chromecast_manager.get_playlist(chromecast_manager.current_playlist)
                    if playlist and chromecast_manager.current_index < len(playlist):
                        playback_status["current_item"] = playlist[chromecast_manager.current_index]
                        
                # Emit status update via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('status_update', playback_status)
                    
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": "Failed to play previous track"})
        except Exception as e:
            logger.error(f"Error in previous_track: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/stop', methods=['POST'])
    def stop_playback():
        """Stop playback on target devices or group"""
        try:
            data = request.get_json(force=True) if request.is_json else {}
            target = data.get('target')
            
            device_names = resolve_target(target)
            if not device_names:
                return jsonify({"success": False, "error": "No valid devices found for target"})
                
            success = chromecast_manager.stop(device_names)
            
            if success:
                playback_status["playing"] = False
                playback_status["connected_devices"] = chromecast_manager.device_statuses
                
                # Emit status update via Socket.IO
                if hasattr(app, 'socketio'):
                    app.socketio.emit('status_update', playback_status)
                    
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": "Failed to stop playback"})
        except Exception as e:
            logger.error(f"Error in stop_playback: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/status', methods=['GET'])
    def get_status():
        """Get current playback status, including per-device and per-group status"""
        try:
            status = playback_status.copy()
            status["connected_devices"] = chromecast_manager.device_statuses.copy()
            status["device_groups"] = chromecast_manager.get_device_groups()
            
            return jsonify({"success": True, "status": status})
        except Exception as e:
            logger.error(f"Error in get_status: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/playback_mode', methods=['POST'])
    def set_playback_mode():
        """Set playback mode (chromecast or web)"""
        try:
            data = request.get_json(force=True)
            mode = data.get('mode')
            
            if mode not in ['chromecast', 'web']:
                return jsonify({"success": False, "error": "Invalid playback mode"})
                
            playback_status["playback_mode"] = mode
            
            # Emit status update via Socket.IO
            if hasattr(app, 'socketio'):
                app.socketio.emit('status_update', playback_status)
                
            return jsonify({"success": True})
        except Exception as e:
            logger.error(f"Error setting playback mode: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    # --- Media File Routes ---
    
    @app.route('/api/media', methods=['GET'])
    def list_media():
        """List all media files in the media directory"""
        try:
            files = []
            for filename in os.listdir(media_dir):
                filepath = os.path.join(media_dir, filename)
                if os.path.isfile(filepath):
                    size = os.path.getsize(filepath)
                    url = f"/media/{filename}"
                    files.append({
                        "filename": filename,
                        "size": size,
                        "url": url
                    })
                    
            return jsonify({"success": True, "files": files})
        except Exception as e:
            logger.error(f"Error listing media files: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/api/upload', methods=['POST'])
    def upload_media():
        """Upload a media file"""
        try:
            if 'file' not in request.files:
                return jsonify({"success": False, "error": "No file part"})
                
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({"success": False, "error": "No selected file"})
                
            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(media_dir, filename)
                file.save(filepath)
                
                url = f"/media/{filename}"
                size = os.path.getsize(filepath)
                
                return jsonify({
                    "success": True,
                    "filename": filename,
                    "size": size,
                    "url": url
                })
        except Exception as e:
            logger.error(f"Error uploading media file: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    @app.route('/media/<filename>')
    def serve_media(filename):
        """Serve a media file"""
        return send_from_directory(media_dir, filename)
    
    # --- Proxy Routes ---
    
    @app.route('/api/proxy')
    def proxy_stream():
        """Proxy streaming for remote media files to avoid CORS issues"""
        url = request.args.get('url')
        
        if not url:
            return jsonify({"success": False, "error": "URL parameter is required"})
            
        try:
            # Parse the URL
            parsed_url = urlparse(url)
            
            # Check if the URL has a valid scheme
            if not parsed_url.scheme or parsed_url.scheme not in ["http", "https"]:
                return jsonify({"success": False, "error": "Invalid URL scheme"})
                
            # Make a HEAD request to get headers
            head_response = requests.head(url, allow_redirects=True, timeout=10)
            
            # Get content type and length
            content_type = head_response.headers.get('Content-Type', 'application/octet-stream')
            content_length = head_response.headers.get('Content-Length')
            
            # Get the range header from the request
            range_header = request.headers.get('Range')
            
            # Prepare headers for the response
            headers = {
                'Content-Type': content_type,
                'Access-Control-Allow-Origin': '*',
                'Accept-Ranges': 'bytes'
            }
            
            # If range header is present, forward it to the remote server
            if range_header:
                headers['Range'] = range_header
                
            # Make the request to the remote server
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            
            # Create a Flask response
            def generate():
                for chunk in response.iter_content(chunk_size=4096):
                    yield chunk
                    
            flask_response = Response(generate(), content_type=content_type)
            
            # Forward relevant headers
            if content_length:
                flask_response.headers['Content-Length'] = content_length
                
            if 'Content-Range' in response.headers:
                flask_response.headers['Content-Range'] = response.headers['Content-Range']
                flask_response.status_code = 206  # Partial Content
                
            return flask_response
            
        except Exception as e:
            logger.error(f"Error proxying stream: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    # --- Static Routes ---
    
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """Serve static files"""
        return send_from_directory(static_dir, filename)
    
    # --- Template Routes ---
    
    @app.route('/templates/<path:filename>')
    def serve_template(filename):
        """Serve template files"""
        return send_from_directory(templates_dir, filename)
