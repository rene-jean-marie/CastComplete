#!/usr/bin/env python3
"""
API Routes Package Initialization
"""

from .firetv import register_firetv_routes

def register_api_routes(app, chromecast_manager, playback_status, static_dir, templates_dir, downloads_dir, media_dir, firetv_manager=None):
    """
    Register all API routes with the Flask app.
    
    Args:
        app: Flask app instance
        chromecast_manager: ChromecastManager instance
        playback_status: Playback status dictionary
        static_dir: Path to static directory
        templates_dir: Path to templates directory
        downloads_dir: Path to downloads directory
        media_dir: Path to media directory
        firetv_manager: Optional FireTVManager instance
    """
    from flask import jsonify, request, send_file, make_response
    import os
    import json
    
    # Register Chromecast API routes
    # (Original API routes remain here)
    
    # API routes for device management
    @app.route('/api/devices', methods=['GET'])
    def get_devices():
        """Get list of available devices."""
        chromecast_devices = chromecast_manager.discover_devices()
        firetv_devices = []
        
        if firetv_manager:
            firetv_devices = firetv_manager.discover_devices()
            
        return jsonify({
            'success': True,
            'devices': {
                'chromecast': chromecast_devices,
                'firetv': firetv_devices
            }
        })
    
    # Other existing API routes remain here...
    
    # Register Fire TV specific routes if the manager is available
    if firetv_manager:
        register_firetv_routes(app, firetv_manager)
