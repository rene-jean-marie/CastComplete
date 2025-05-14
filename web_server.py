#!/usr/bin/env python3
"""
Web Server Entry Point for CastComplete
"""

from chromecast_web_playlist.web import run_server


def main():
    """Main entry point for the web server."""
    print("Starting CastComplete web server...")
    run_server(host="0.0.0.0", port=5001, debug=True)


if __name__ == "__main__":
    main()
