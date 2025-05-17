#!/usr/bin/env python3
"""
Fire TV API Routes
API routes for Fire TV device management
"""

import json
import logging
from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

# Create blueprint
firetv_api = Blueprint('firetv_api', __name__)

def register_firetv_routes(app, firetv_manager):
    """Register Fire TV API routes with the Flask app."""
    
    @firetv_api.route('/api/firetv/devices', methods=['GET'])
    def get_devices():
        """Get list of saved Fire TV devices."""
        devices = firetv_manager.discover_devices()
        return jsonify({
            'success': True,
            'devices': devices
        })
    
    @firetv_api.route('/api/firetv/device', methods=['POST'])
    def add_device():
        """Add a new Fire TV device."""
        data = request.json
        
        if not data or 'name' not in data or 'host' not in data:
            return jsonify({
                'success': False, 
                'error': 'Missing required fields: name, host'
            }), 400
            
        name = data['name']
        host = data['host']
        port = data.get('port', 5555)
        
        success = firetv_manager.save_device(name, host, port)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Device {name} added successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to add device {name}'
            }), 500
    
    @firetv_api.route('/api/firetv/device/<name>', methods=['DELETE'])
    def remove_device(name):
        """Remove a Fire TV device."""
        success = firetv_manager.remove_device(name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Device {name} removed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to remove device {name}'
            }), 404
    
    @firetv_api.route('/api/firetv/connect', methods=['POST'])
    def connect():
        """Connect to a Fire TV device."""
        data = request.json
        
        if not data or 'name' not in data:
            return jsonify({
                'success': False, 
                'error': 'Missing required field: name'
            }), 400
            
        success = firetv_manager.connect(data['name'])
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Connected to {data["name"]}'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to connect to {data["name"]}'
            }), 500
    
    @firetv_api.route('/api/firetv/disconnect', methods=['POST'])
    def disconnect():
        """Disconnect from a Fire TV device."""
        data = request.json
        name = data.get('name') if data else None
        
        success = firetv_manager.disconnect(name)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Disconnected successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to disconnect'
            }), 500
    
    @firetv_api.route('/api/firetv/status', methods=['GET'])
    def status():
        """Get status of a Fire TV device."""
        name = request.args.get('name')
        status = firetv_manager.get_status(name)
        
        if 'error' not in status:
            return jsonify({
                'success': True,
                'status': status
            })
        else:
            return jsonify({
                'success': False,
                'error': status['error']
            }), 404
    
    @firetv_api.route('/api/firetv/control', methods=['POST'])
    def control():
        """Control a Fire TV device."""
        data = request.json
        
        if not data or 'command' not in data:
            return jsonify({
                'success': False, 
                'error': 'Missing required field: command'
            }), 400
        
        command = data['command']
        device = data.get('device')
        success = False
        
        if command == 'play':
            success = firetv_manager.play(device)
        elif command == 'pause':
            success = firetv_manager.pause(device)
        elif command == 'stop':
            success = firetv_manager.stop(device)
        elif command == 'next':
            success = firetv_manager.next(device)
        elif command == 'previous':
            success = firetv_manager.previous(device)
        elif command == 'home':
            success = firetv_manager.home(device)
        elif command == 'launch':
            app_id = data.get('app_id')
            if not app_id:
                return jsonify({
                    'success': False,
                    'error': 'Missing required field for launch command: app_id'
                }), 400
            success = firetv_manager.launch_app(app_id, device)
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown command: {command}'
            }), 400
        
        if success:
            return jsonify({
                'success': True,
                'message': f'{command} command sent successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to send {command} command'
            }), 500
    
    # Register the blueprint
    app.register_blueprint(firetv_api)
