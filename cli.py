#!/usr/bin/env python3
"""
Command Line Interface for CastComplete
"""

# Import CLI from the package structure
from chromecast_web_playlist.cli import main as cli_main


def main():
    """Main entry point for the CLI."""
    # Use the CLI implementation from the package structure
    cli_main()


if __name__ == "__main__":
    main()
