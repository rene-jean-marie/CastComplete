#!/usr/bin/env python3
"""
CLI Commands
Command-line interface for the Chromecast Web Playlist Manager
"""

import os
import sys
import argparse
import logging
import time
from typing import Dict, List, Optional, Any, Union

from ..core.chromecast_manager import ChromecastManager
from ..core.firetv_manager import FireTVManager
from ..extractors.media_extractor import extract_media, extract_x_feed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CLI:
    """
    Command-line interface for the Chromecast Web Playlist Manager.
    """
    
    def __init__(self):
        """Initialize the CLI."""
        self.chromecast_manager = ChromecastManager()
        self.firetv_manager = FireTVManager()
        self.parser = self._create_parser()
        
    def _create_parser(self):
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description="Chromecast Web Playlist Manager CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Command to execute")
        
        # Devices commands
        devices_parser = subparsers.add_parser("devices", help="List available Chromecast devices")
        
        connect_parser = subparsers.add_parser("connect", help="Connect to a Chromecast device")
        connect_parser.add_argument("device", help="Name of the device to connect to")
        
        disconnect_parser = subparsers.add_parser("disconnect", help="Disconnect from a Chromecast device")
        disconnect_parser.add_argument("device", nargs="?", help="Name of the device to disconnect from (optional)")
        
        # Device group commands
        groups_parser = subparsers.add_parser("groups", help="List device groups")
        
        create_group_parser = subparsers.add_parser("create-group", help="Create a device group")
        create_group_parser.add_argument("name", help="Name of the group")
        create_group_parser.add_argument("devices", nargs="*", help="Names of devices to add to the group")
        
        delete_group_parser = subparsers.add_parser("delete-group", help="Delete a device group")
        delete_group_parser.add_argument("name", help="Name of the group")
        
        add_to_group_parser = subparsers.add_parser("add-to-group", help="Add a device to a group")
        add_to_group_parser.add_argument("group", help="Name of the group")
        add_to_group_parser.add_argument("devices", nargs="+", help="Names of devices to add")
        
        remove_from_group_parser = subparsers.add_parser("remove-from-group", help="Remove a device from a group")
        remove_from_group_parser.add_argument("group", help="Name of the group")
        remove_from_group_parser.add_argument("devices", nargs="+", help="Names of devices to remove")
        
        sync_group_parser = subparsers.add_parser("sync-group", help="Synchronize playback across devices in a group")
        sync_group_parser.add_argument("name", help="Name of the group")
        
        # Playlist commands
        playlists_parser = subparsers.add_parser("playlists", help="List available playlists")
        
        create_parser = subparsers.add_parser("create", help="Create a new playlist")
        create_parser.add_argument("name", help="Name of the playlist")
        
        delete_parser = subparsers.add_parser("delete", help="Delete a playlist")
        delete_parser.add_argument("name", help="Name of the playlist")
        
        view_parser = subparsers.add_parser("view", help="View playlist contents")
        view_parser.add_argument("name", help="Name of the playlist")
        
        add_parser = subparsers.add_parser("add", help="Add media to a playlist")
        add_parser.add_argument("playlist", help="Name of the playlist")
        add_parser.add_argument("url", help="URL of the media")
        add_parser.add_argument("--title", help="Title of the media")
        add_parser.add_argument("--extract", action="store_true", help="Extract media from web page")
        add_parser.add_argument("--validate", action="store_true", help="Validate media URL")
        
        remove_parser = subparsers.add_parser("remove", help="Remove an item from a playlist")
        remove_parser.add_argument("playlist", help="Name of the playlist")
        remove_parser.add_argument("index", type=int, help="Index of the item to remove")
        
        # Extract commands
        extract_parser = subparsers.add_parser("extract", help="Extract media from a URL")
        extract_parser.add_argument("url", help="URL to extract media from")
        extract_parser.add_argument("--save", help="Save extracted media to a playlist")
        extract_parser.add_argument("--scroll", type=int, default=5, help="Number of times to scroll (for X feeds)")
        
        # Playback commands
        load_parser = subparsers.add_parser("load", help="Load a playlist")
        load_parser.add_argument("name", help="Name of the playlist")
        load_parser.add_argument("--device", help="Target device")
        load_parser.add_argument("--group", help="Target device group")
        
        play_parser = subparsers.add_parser("play", help="Start playback")
        play_parser.add_argument("--device", help="Target device")
        play_parser.add_argument("--group", help="Target device group")
        
        pause_parser = subparsers.add_parser("pause", help="Pause playback")
        pause_parser.add_argument("--device", help="Target device")
        pause_parser.add_argument("--group", help="Target device group")
        
        resume_parser = subparsers.add_parser("resume", help="Resume playback")
        resume_parser.add_argument("--device", help="Target device")
        resume_parser.add_argument("--group", help="Target device group")
        
        stop_parser = subparsers.add_parser("stop", help="Stop playback")
        stop_parser.add_argument("--device", help="Target device")
        stop_parser.add_argument("--group", help="Target device group")
        
        next_parser = subparsers.add_parser("next", help="Play next track")
        next_parser.add_argument("--device", help="Target device")
        next_parser.add_argument("--group", help="Target device group")
        
        prev_parser = subparsers.add_parser("prev", help="Play previous track")
        prev_parser.add_argument("--device", help="Target device")
        prev_parser.add_argument("--group", help="Target device group")
        
        # Web server commands with subcommands
        server_parser = subparsers.add_parser("server", help="Web server management")
        server_subparsers = server_parser.add_subparsers(dest="server_command", help="Server command")
        
        # Start server command
        start_parser = server_subparsers.add_parser("start", help="Start the web server")
        start_parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
        start_parser.add_argument("--port", type=int, default=5001, help="Port to bind the server to")
        start_parser.add_argument("--debug", action="store_true", help="Run in debug mode")
        
        # Stop server command
        stop_parser = server_subparsers.add_parser("stop", help="Stop the web server")
        
        # Restart server command
        restart_parser = server_subparsers.add_parser("restart", help="Restart the web server")
        restart_parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
        restart_parser.add_argument("--port", type=int, default=5001, help="Port to bind the server to")
        restart_parser.add_argument("--debug", action="store_true", help="Run in debug mode")
        
        # Fire TV commands
        firetv_parser = subparsers.add_parser("firetv", help="Fire TV device management")
        firetv_subparsers = firetv_parser.add_subparsers(dest="firetv_command", help="Fire TV command")
        
        # Fire TV list devices command
        firetv_list_parser = firetv_subparsers.add_parser("list", help="List saved Fire TV devices")
        
        # Fire TV discover command
        firetv_discover_parser = firetv_subparsers.add_parser("discover", help="Discover Fire TV devices on the network")
        firetv_discover_parser.add_argument("--network", help="Network to scan in CIDR notation (e.g. 192.168.1.0/24)")
        firetv_discover_parser.add_argument("--timeout", type=int, default=2, help="Timeout for scanning in seconds (default: 2)")
        
        # Fire TV add device command
        firetv_add_parser = firetv_subparsers.add_parser("add", help="Add a new Fire TV device")
        firetv_add_parser.add_argument("name", help="Friendly name for the device")
        firetv_add_parser.add_argument("host", help="IP address of the device")
        firetv_add_parser.add_argument("--port", type=int, default=5555, help="ADB port (default: 5555)")
        
        # Fire TV remove device command
        firetv_remove_parser = firetv_subparsers.add_parser("remove", help="Remove a saved Fire TV device")
        firetv_remove_parser.add_argument("name", help="Name of the device to remove")
        
        # Fire TV connect command
        firetv_connect_parser = firetv_subparsers.add_parser("connect", help="Connect to a Fire TV device")
        firetv_connect_parser.add_argument("name", help="Name of the device to connect to")
        
        # Fire TV disconnect command
        firetv_disconnect_parser = firetv_subparsers.add_parser("disconnect", help="Disconnect from a Fire TV device")
        firetv_disconnect_parser.add_argument("name", nargs="?", help="Name of the device to disconnect from (optional)")
        
        # Fire TV status command
        firetv_status_parser = firetv_subparsers.add_parser("status", help="Get status of a Fire TV device")
        firetv_status_parser.add_argument("name", nargs="?", help="Name of the device (optional)")
        
        # Fire TV media control commands
        firetv_play_parser = firetv_subparsers.add_parser("play", help="Play media on Fire TV")
        firetv_play_parser.add_argument("name", nargs="?", help="Target device name (optional)")
        
        firetv_pause_parser = firetv_subparsers.add_parser("pause", help="Pause media on Fire TV")
        firetv_pause_parser.add_argument("name", nargs="?", help="Target device name (optional)")
        
        firetv_stop_parser = firetv_subparsers.add_parser("stop", help="Stop media on Fire TV")
        firetv_stop_parser.add_argument("name", nargs="?", help="Target device name (optional)")
        
        firetv_next_parser = firetv_subparsers.add_parser("next", help="Skip to next media on Fire TV")
        firetv_next_parser.add_argument("name", nargs="?", help="Target device name (optional)")
        
        firetv_previous_parser = firetv_subparsers.add_parser("previous", help="Go to previous media on Fire TV")
        firetv_previous_parser.add_argument("name", nargs="?", help="Target device name (optional)")
        
        firetv_home_parser = firetv_subparsers.add_parser("home", help="Press home button on Fire TV")
        firetv_home_parser.add_argument("name", nargs="?", help="Target device name (optional)")
        
        firetv_launch_parser = firetv_subparsers.add_parser("launch", help="Launch an app on Fire TV")
        firetv_launch_parser.add_argument("app_id", help="Application ID to launch")
        firetv_launch_parser.add_argument("--name", help="Target device name (optional)")
        
        return parser
        
    def _resolve_target(self, args):
        """
        Resolve the target device or group from command-line arguments.
        
        Args:
            args: Command-line arguments
            
        Returns:
            Target device or group name, or None
        """
        if hasattr(args, "device") and args.device:
            return args.device
        elif hasattr(args, "group") and args.group:
            if args.group in self.chromecast_manager.device_groups:
                return self.chromecast_manager.device_groups[args.group]
            else:
                logger.error(f"Group {args.group} does not exist")
                return None
        else:
            return None
        
    def run(self, args=None):
        """
        Run the CLI with the given arguments.
        
        Args:
            args: Command-line arguments (optional)
        """
        if args is None:
            args = self.parser.parse_args()
        else:
            args = self.parser.parse_args(args)
            
        if not args.command:
            self.parser.print_help()
            return
            
        # Device commands
        if args.command == "devices":
            devices = self.chromecast_manager.discover_devices()
            if devices:
                print("Available devices:")
                for device in devices:
                    print(f"  - {device}")
            else:
                print("No devices found")
                
        elif args.command == "connect":
            success = self.chromecast_manager.connect(args.device)
            if success:
                print(f"Connected to {args.device}")
            else:
                print(f"Failed to connect to {args.device}")
                
        elif args.command == "disconnect":
            success = self.chromecast_manager.disconnect(args.device)
            if success:
                if args.device:
                    print(f"Disconnected from {args.device}")
                else:
                    print("Disconnected from all devices")
            else:
                print("Failed to disconnect")
                
        # Device group commands
        elif args.command == "groups":
            groups = self.chromecast_manager.get_device_groups()
            if groups:
                print("Device groups:")
                for name, devices in groups.items():
                    print(f"  - {name}: {', '.join(devices)}")
            else:
                print("No device groups")
                
        elif args.command == "create-group":
            success = self.chromecast_manager.create_device_group(args.name, args.devices)
            if success:
                print(f"Created group {args.name}")
            else:
                print(f"Failed to create group {args.name}")
                
        elif args.command == "delete-group":
            success = self.chromecast_manager.delete_device_group(args.name)
            if success:
                print(f"Deleted group {args.name}")
            else:
                print(f"Failed to delete group {args.name}")
                
        elif args.command == "add-to-group":
            success = True
            for device in args.devices:
                if not self.chromecast_manager.add_to_device_group(args.group, device):
                    success = False
                    print(f"Failed to add {device} to group {args.group}")
            if success:
                print(f"Added devices to group {args.group}")
                
        elif args.command == "remove-from-group":
            success = True
            for device in args.devices:
                if not self.chromecast_manager.remove_from_device_group(args.group, device):
                    success = False
                    print(f"Failed to remove {device} from group {args.group}")
            if success:
                print(f"Removed devices from group {args.group}")
                
        elif args.command == "sync-group":
            success = self.chromecast_manager.sync_device_group(args.name)
            if success:
                print(f"Synchronized group {args.name}")
            else:
                print(f"Failed to synchronize group {args.name}")
                
        # Playlist commands
        elif args.command == "playlists":
            playlists = self.chromecast_manager.get_playlists()
            if playlists:
                print("Available playlists:")
                for playlist in playlists:
                    print(f"  - {playlist}")
            else:
                print("No playlists")
                
        elif args.command == "create":
            success = self.chromecast_manager.create_playlist(args.name)
            if success:
                print(f"Created playlist {args.name}")
            else:
                print(f"Failed to create playlist {args.name}")
                
        elif args.command == "delete":
            success = self.chromecast_manager.delete_playlist(args.name)
            if success:
                print(f"Deleted playlist {args.name}")
            else:
                print(f"Failed to delete playlist {args.name}")
                
        elif args.command == "view":
            playlist = self.chromecast_manager.get_playlist(args.name)
            if playlist:
                print(f"Playlist: {args.name}")
                for i, item in enumerate(playlist):
                    print(f"  {i}. {item['title']} ({item['url']})")
            else:
                print(f"Playlist {args.name} not found")
                
        elif args.command == "add":
            if args.extract:
                # Extract media from URL
                result = extract_media(args.url)
                if result["media_urls"]:
                    for media in result["media_urls"]:
                        title = args.title or result["title"]
                        success = self.chromecast_manager.add_to_playlist(args.playlist, media["url"], title)
                        if success:
                            print(f"Added {media['url']} to playlist {args.playlist}")
                        else:
                            print(f"Failed to add {media['url']} to playlist {args.playlist}")
                else:
                    print(f"No media found at {args.url}")
            else:
                # Add URL directly
                success = self.chromecast_manager.add_to_playlist(args.playlist, args.url, args.title)
                if success:
                    print(f"Added {args.url} to playlist {args.playlist}")
                else:
                    print(f"Failed to add {args.url} to playlist {args.playlist}")
                    
        elif args.command == "remove":
            success = self.chromecast_manager.remove_from_playlist(args.playlist, args.index)
            if success:
                print(f"Removed item {args.index} from playlist {args.playlist}")
            else:
                print(f"Failed to remove item {args.index} from playlist {args.playlist}")
                
        # Extract commands
        elif args.command == "extract":
            if "twitter.com" in args.url or "x.com" in args.url:
                if "/status/" not in args.url:
                    # Extract from X feed
                    results = extract_x_feed(args.url, args.scroll)
                    if results:
                        print(f"Extracted {len(results)} videos from X feed")
                        for i, result in enumerate(results):
                            print(f"  {i}. {result['title']}")
                            if args.save:
                                for media in result["media_urls"]:
                                    success = self.chromecast_manager.add_to_playlist(args.save, media["url"], result["title"])
                                    if success:
                                        print(f"    Added to playlist {args.save}")
                    else:
                        print("No videos found in X feed")
                else:
                    # Extract from X post
                    result = extract_media(args.url)
                    if result["media_urls"]:
                        print(f"Extracted {len(result['media_urls'])} media URLs from {args.url}")
                        for i, media in enumerate(result["media_urls"]):
                            print(f"  {i}. {media['url']}")
                            if args.save:
                                success = self.chromecast_manager.add_to_playlist(args.save, media["url"], result["title"])
                                if success:
                                    print(f"    Added to playlist {args.save}")
                    else:
                        print(f"No media found at {args.url}")
            else:
                # Extract from web page
                result = extract_media(args.url)
                if result["media_urls"]:
                    print(f"Extracted {len(result['media_urls'])} media URLs from {args.url}")
                    for i, media in enumerate(result["media_urls"]):
                        print(f"  {i}. {media['url']}")
                        if args.save:
                            success = self.chromecast_manager.add_to_playlist(args.save, media["url"], result["title"])
                            if success:
                                print(f"    Added to playlist {args.save}")
                else:
                    print(f"No media found at {args.url}")
                    
        # Playback commands
        elif args.command == "load":
            target = self._resolve_target(args)
            success = self.chromecast_manager.load_playlist(args.name, target)
            if success:
                print(f"Loaded playlist {args.name}")
            else:
                print(f"Failed to load playlist {args.name}")
                
        elif args.command == "play":
            target = self._resolve_target(args)
            success = self.chromecast_manager.play(target)
            if success:
                print("Playback started")
            else:
                print("Failed to start playback")
                
        elif args.command == "pause":
            target = self._resolve_target(args)
            success = self.chromecast_manager.pause(target)
            if success:
                print("Playback paused")
            else:
                print("Failed to pause playback")
                
        elif args.command == "resume":
            target = self._resolve_target(args)
            success = self.chromecast_manager.resume(target)
            if success:
                print("Playback resumed")
            else:
                print("Failed to resume playback")
                
        elif args.command == "stop":
            target = self._resolve_target(args)
            success = self.chromecast_manager.stop(target)
            if success:
                print("Playback stopped")
            else:
                print("Failed to stop playback")
                
        elif args.command == "next":
            target = self._resolve_target(args)
            success = self.chromecast_manager.next(target)
            if success:
                print("Playing next track")
            else:
                print("Failed to play next track")
                
        elif args.command == "prev":
            target = self._resolve_target(args)
            success = self.chromecast_manager.previous(target)
            if success:
                print("Playing previous track")
            else:
                print("Failed to play previous track")
                
        # Web server commands with subcommands
        elif args.command == "server":
            import os
            import signal
            import psutil
            import subprocess
            import time
            from ..web import run_server
            
            # Helper function to stop running server
            def stop_server():
                server_found = False
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = proc.info['cmdline']
                        if cmdline and len(cmdline) > 1:
                            cmd_str = ' '.join(cmdline)
                            if 'chromecast-server' in cmd_str or 'chromecast_web_playlist.web.server' in cmd_str:
                                print(f"Found server process (PID: {proc.info['pid']}), stopping it...")
                                os.kill(proc.info['pid'], signal.SIGTERM)
                                server_found = True
                                # Give it a moment to stop
                                time.sleep(1)
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                return server_found
            
            if not hasattr(args, 'server_command') or not args.server_command:
                print("Error: Please specify a server subcommand (start/stop/restart)")
                return
                
            # Start the server
            if args.server_command == "start":
                print(f"Starting web server on {args.host}:{args.port}")
                run_server(args.host, args.port, args.debug)
                
            # Stop the server
            elif args.server_command == "stop":
                if stop_server():
                    print("Server stopped successfully")
                else:
                    print("No running server found")
                    
            # Restart the server
            elif args.server_command == "restart":
                server_found = stop_server()
                if not server_found:
                    print("No running server found to restart")
                
                # Start a new server
                print(f"Starting web server on {args.host}:{args.port}")
                run_server(args.host, args.port, args.debug)
                
        # Fire TV commands
        elif args.command == "firetv":
            if not hasattr(args, 'firetv_command') or not args.firetv_command:
                print("Error: Please specify a Fire TV subcommand")
                return
            
            # List saved Fire TV devices
            if args.firetv_command == "list":
                devices = self.firetv_manager.discover_devices()
                if devices:
                    print("Saved Fire TV devices:")
                    for device in devices:
                        print(f"  - {device}")
                else:
                    print("No saved Fire TV devices")
            
            # Discover Fire TV devices on the network
            elif args.firetv_command == "discover":
                print("Scanning network for Fire TV devices...")
                network = args.network if hasattr(args, 'network') and args.network else None
                timeout = args.timeout if hasattr(args, 'timeout') else 2
                
                devices = self.firetv_manager.scan_network(network, timeout)
                
                if devices:
                    print(f"\nDiscovered {len(devices)} potential Fire TV devices:")
                    print("-" * 60)
                    print(f"{'IP Address':<15} {'Name':<25} {'Status':<10} {'Saved Name':<15}")
                    print("-" * 60)
                    
                    for device in devices:
                        status = "Saved" if device['saved'] else "New"
                        saved_name = device['saved_name'] if device['saved'] else "-"
                        print(f"{device['ip']:<15} {device['name']:<25} {status:<10} {saved_name:<15}")
                    
                    print("\nTo add a device, use: castcomplete firetv add <name> <ip>")
                else:
                    print("\nNo Fire TV devices found on the network.")
                    print("Make sure your Fire TV devices have ADB debugging enabled.")
                    print("You can manually add a device using: castcomplete firetv add <name> <ip>")
                    
                print("\nNote: Fire TV devices must have ADB debugging enabled in Settings > My Fire TV > Developer options")
            
            # Add a new Fire TV device
            elif args.firetv_command == "add":
                success = self.firetv_manager.save_device(
                    args.name, args.host, args.port)
                if success:
                    print(f"Added Fire TV device: {args.name}")
                else:
                    print(f"Failed to add Fire TV device: {args.name}")
            
            # Remove a saved Fire TV device
            elif args.firetv_command == "remove":
                success = self.firetv_manager.remove_device(args.name)
                if success:
                    print(f"Removed Fire TV device: {args.name}")
                else:
                    print(f"Failed to remove Fire TV device: {args.name}")
            
            # Connect to a Fire TV device
            elif args.firetv_command == "connect":
                success = self.firetv_manager.connect(args.name)
                if success:
                    print(f"Connected to Fire TV device: {args.name}")
                else:
                    print(f"Failed to connect to Fire TV device: {args.name}")
            
            # Disconnect from a Fire TV device
            elif args.firetv_command == "disconnect":
                success = self.firetv_manager.disconnect(args.name)
                if success:
                    if args.name:
                        print(f"Disconnected from Fire TV device: {args.name}")
                    else:
                        print("Disconnected from all Fire TV devices")
                else:
                    print(f"Failed to disconnect from Fire TV device")
            
            # Get status of a Fire TV device
            elif args.firetv_command == "status":
                status = self.firetv_manager.get_status(args.name)
                if "error" not in status:
                    print(f"Fire TV status: {status}")
                else:
                    print(f"Error getting status: {status['error']}")
            
            # Fire TV media control commands
            elif args.firetv_command == "play":
                success = self.firetv_manager.play(args.name)
                if success:
                    print("Play command sent successfully")
                else:
                    print("Failed to send play command")
            
            elif args.firetv_command == "pause":
                success = self.firetv_manager.pause(args.name)
                if success:
                    print("Pause command sent successfully")
                else:
                    print("Failed to send pause command")
            
            elif args.firetv_command == "stop":
                success = self.firetv_manager.stop(args.name)
                if success:
                    print("Stop command sent successfully")
                else:
                    print("Failed to send stop command")
            
            elif args.firetv_command == "next":
                success = self.firetv_manager.next(args.name)
                if success:
                    print("Next command sent successfully")
                else:
                    print("Failed to send next command")
            
            elif args.firetv_command == "previous":
                success = self.firetv_manager.previous(args.name)
                if success:
                    print("Previous command sent successfully")
                else:
                    print("Failed to send previous command")
            
            elif args.firetv_command == "home":
                success = self.firetv_manager.home(args.name)
                if success:
                    print("Home button pressed successfully")
                else:
                    print("Failed to send home command")
            
            elif args.firetv_command == "launch":
                device_name = args.name if hasattr(args, 'name') else None
                success = self.firetv_manager.launch_app(args.app_id, device_name)
                if success:
                    print(f"Launched app: {args.app_id}")
                else:
                    print(f"Failed to launch app: {args.app_id}")
            
def main():
    """Main entry point for the CLI."""
    cli = CLI()
    cli.run()
    
if __name__ == "__main__":
    main()
