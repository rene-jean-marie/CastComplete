#!/usr/bin/env python3
"""
CastComplete - Chromecast Playlist Manager
Main entry point for the application
"""

import sys
import argparse

from chromecast_web_playlist.core import ChromecastManager
from chromecast_web_playlist.web import run_server
from chromecast_web_playlist.cli import main as cli_main

def main():
    """
    Main entry point for the application.
    Parses command-line arguments and runs the appropriate command.
    """
    parser = argparse.ArgumentParser(
        description="CastComplete - Chromecast Playlist Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--web", "-w", action="store_true",
        help="Start the web server"
    )
    parser.add_argument(
        "--host", default="0.0.0.0",
        help="Host to bind the web server to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=5001,
        help="Port to bind the web server to (default: 5001)"
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Run in debug mode"
    )
    
    # Parse args and handle default behavior
    if len(sys.argv) == 1:
        # No arguments, default to web server
        args = parser.parse_args(["--web"])
    else:
        args = parser.parse_args()
    
    if args.web:
        # Start the web server
        print(f"Starting CastComplete web server on {args.host}:{args.port}")
        run_server(args.host, args.port, args.debug)
    else:
        # Run the CLI
        cli_main()

if __name__ == "__main__":
    main()
