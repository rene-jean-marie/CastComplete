#!/usr/bin/env python3
"""
Web Server Component
Flask web server for the Chromecast Web Playlist Manager
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

# Flask imports
from flask import Flask, render_template, request, jsonify, send_from_directory, Response
from flask_socketio import SocketIO, emit

# Import the managers
from ..core.chromecast_manager import ChromecastManager
from ..core.firetv_manager import FireTVManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebServer:
    """
    Flask web server for the Chromecast Web Playlist Manager.
    """
    
    def __init__(self, chromecast_manager: ChromecastManager, host: str = '0.0.0.0', port: int = 5001, firetv_manager: Optional[FireTVManager] = None):
        """
        Initialize the WebServer.
        
        Args:
            chromecast_manager: ChromecastManager instance
            host: Host to bind the server to
            port: Port to bind the server to
            firetv_manager: Optional FireTVManager instance
        """
        self.chromecast_manager = chromecast_manager
        self.firetv_manager = firetv_manager or FireTVManager()
        self.host = host
        self.port = port
        
        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'chromecast-web-server-playlist'
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 * 1024  # 16GB max upload size
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Current playback status
        self.playback_status = {
            "playing": False,
            "current_playlist": None,
            "current_index": 0,
            "current_item": None,
            "connected_devices": {},  # Dict of device_name: status_obj
            "device_groups": {},      # Dict of group_name: [device_names]
            "active_device": None,    # Currently selected device
            "active_group": None,     # Currently selected group
            "web_player_active": False,
            "playback_mode": "chromecast",  # 'chromecast' or 'web'
            "current_playlist_items": [],  # Store the current playlist items for reference
            "synchronization_active": False  # Whether automatic synchronization is active
        }
        
        # Path to static files and templates
        self.static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        self.templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        
        # Path to downloads directory
        self.downloads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'downloads')
        os.makedirs(self.downloads_dir, exist_ok=True)
        
        # Path to media directory for local files
        self.media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'media')
        os.makedirs(self.media_dir, exist_ok=True)
        
        # Register routes
        self._register_routes()
        
        # Register Socket.IO events
        self._register_socketio_events()
        
    def _register_routes(self):
        """Register Flask routes."""
        # Main route
        @self.app.route('/')
        def index():
            """Render the main page"""
            return render_template('index.html')
            
        # Server control route - allows stopping the server remotely
        @self.app.route('/api/admin/server/control', methods=['POST'])
        def server_control():
            """Control the server remotely"""
            if not request.is_json:
                return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
                
            data = request.json
            action = data.get('action')
            secret = data.get('secret')
            
            # Simple security check - should be enhanced in production
            # The secret is just 'castcomplete' for demonstration
            if secret != 'castcomplete':
                return jsonify({'success': False, 'error': 'Invalid authentication'}), 403
                
            if action == 'stop':
                # Schedule server shutdown after response is sent
                def shutdown_server():
                    import os
                    import signal
                    import time
                    logger.info('Server shutdown requested via API')
                    time.sleep(1)  # Brief delay to allow response to be sent
                    os.kill(os.getpid(), signal.SIGTERM)
                
                from threading import Thread
                Thread(target=shutdown_server).start()
                return jsonify({'success': True, 'message': 'Server shutdown initiated'})
            else:
                return jsonify({'success': False, 'error': f'Unknown action: {action}'}), 400
            
        # API routes
        from .api import register_api_routes
        register_api_routes(self.app, self.chromecast_manager, self.playback_status, 
                           self.static_dir, self.templates_dir, self.downloads_dir, self.media_dir,
                           self.firetv_manager)
                           
    def _register_socketio_events(self):
        """Register Socket.IO events."""
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            logger.info('Client connected')
            
            # Send initial status
            emit('status_update', self.playback_status)
            
            # Send initial playlists
            playlists = self.chromecast_manager.get_playlists()
            emit('playlists_initial', {'playlists': playlists})
            
            # Send initial playlist content if available
            if self.playback_status['current_playlist']:
                playlist = self.playback_status['current_playlist']
                items = self.chromecast_manager.get_playlist(playlist)
                emit('playlist_content_initial', {'playlist': playlist, 'items': items})
                
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            logger.info('Client disconnected')
            
        @self.socketio.on('request_playlist_content')
        def handle_request_playlist_content(data):
            """Handle request for playlist content"""
            playlist = data.get('playlist')
            if playlist:
                items = self.chromecast_manager.get_playlist(playlist)
                emit('playlist_content_response', {'playlist': playlist, 'items': items})
                
    def run(self, debug: bool = True):
        """
        Run the web server.
        
        Args:
            debug: Whether to run in debug mode
        """
        try:
            logger.info(f"Starting web server on {self.host}:{self.port}")
            self.socketio.run(self.app, host=self.host, port=self.port, debug=debug, allow_unsafe_werkzeug=True)
        except Exception as e:
            logger.error(f"Error running web server: {e}")
            
def create_server(chromecast_manager: ChromecastManager = None, host: str = '0.0.0.0', port: int = 5001, firetv_manager: FireTVManager = None):
    """
    Create a web server instance.
    
    Args:
        chromecast_manager: ChromecastManager instance (optional)
        host: Host to bind the server to
        port: Port to bind the server to
        firetv_manager: FireTVManager instance (optional)
        
    Returns:
        WebServer instance
    """
    if chromecast_manager is None:
        chromecast_manager = ChromecastManager()
        
    if firetv_manager is None:
        firetv_manager = FireTVManager()
        
    return WebServer(chromecast_manager, host, port, firetv_manager)
    
def run_server(host: str = '0.0.0.0', port: int = 5001, debug: bool = True):
    """
    Create and run a web server.
    
    Args:
        host: Host to bind the server to
        port: Port to bind the server to
        debug: Whether to run in debug mode
    """
    server = create_server(host=host, port=port)
    server.run(debug=debug)
