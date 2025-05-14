# CastComplete

A powerful Chromecast playlist manager with web scraping capabilities, multi-device playback support, and a web server interface accessible from multiple devices. CastComplete allows you to create synchronized playback experiences across both Chromecast devices and web clients (laptops, phones, tablets).

## Features

- Discover and connect to Chromecast devices
- Register web clients (laptops, phones, tablets) as playback devices
- Create and manage device groups with both Chromecast devices and web clients
- Play media on multiple devices simultaneously with synchronized playback
- Create and manage playlists with easy drag-and-drop reordering
- Extract media URLs from web pages automatically
- Extract videos from X (Twitter) posts and feeds
- Validate media URLs before adding to playlists
- Control playback (play, pause, next, previous) on individual devices or groups
- Support for HLS/m3u8 streams and various media formats
- Access and control from any device on your network via responsive web interface
- Monitor per-device playback status in real-time with detailed feedback
- Refresh functionality for device groups and playlists

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/rene-jean-marie/CastComplete.git
cd CastComplete

# Create and activate virtual environment
uv init CastComplete
uv venv
source .venv/bin/activate

# Install the package in development mode
uv pip install -e .

# Install Playwright browser
python -m playwright install chromium
```

## Usage

### Web Server

Start the web server to access the playlist manager from any device on your network:

```bash
# Using the entry point script
castserver

# Or directly with Python
python web_server.py
```

Then open a web browser and navigate to:
```
http://<server-ip>:5001
```

The web interface allows you to:
- Discover and connect to Chromecast devices
- Register the current device (laptop, phone, tablet) as a web client
- Create and manage device groups that include both Chromecast devices and web clients
- Select individual devices or groups as playback targets
- Create and manage playlists with drag-and-drop reordering
- Add media URLs to playlists with automatic extraction
- Upload media files directly to the server
- Control playback (play, pause, stop, next, previous) on individual devices or groups
- Monitor per-device playback status in real-time with detailed feedback
- Synchronize playback across all devices in a group
- Refresh device groups and playlists with dedicated buttons

### Command Line Interface

The project includes a comprehensive CLI:

```bash
# Using the entry point script
castcomplete devices

# Or directly with Python
python cli.py devices
```

#### Device Management:
```bash
# List available Chromecast devices
castcomplete devices

# Connect to a device
castcomplete connect "Living Room TV"

# Create a device group
castcomplete create-group "Living Room Group"

# Add devices to a group
castcomplete add-to-group "Living Room Group" "Living Room TV" "Kitchen Speaker"

# Remove a device from a group
castcomplete remove-from-group "Living Room Group" "Kitchen Speaker"

# Delete a device group
castcomplete delete-group "Living Room Group"
```

#### Playlist Management:
```bash
# List available playlists
castcomplete playlists

# Create a new playlist
castcomplete create my_playlist

# View playlist contents
castcomplete view my_playlist

# Add media URL directly
castcomplete add my_playlist http://example.com/video.mp4 --title "My Video"

# Extract and add media from a web page
castcomplete add my_playlist https://example.com/page-with-video --extract
```

#### Playback Control:
```bash
# Load a playlist
castcomplete load my_playlist

# Start playback on a specific device
castcomplete play --device "Living Room TV"

# Start playback on a device group
castcomplete play --group "Living Room Group"

# Control playback
castcomplete pause --group "Living Room Group"
castcomplete resume --group "Living Room Group"
castcomplete next --device "Living Room TV"
```

## Web Client Registration and Device Groups

CastComplete allows you to register any device with a web browser as a playback client, enabling synchronized multi-device experiences without requiring Chromecast hardware.

### Registering Web Clients

1. Open the CastComplete web interface on any device (laptop, phone, tablet)
2. Click the "Register This Device" button
3. Your device will appear in the device list with a 💻 icon
4. You can unregister at any time by clicking the "Unregister" button

### Creating Device Groups

Device groups allow you to play media on multiple devices simultaneously:

1. Enter a name in the "New group name" field
2. Click "Create Group"
3. Select one or more devices from the device list
4. Click "Add Device(s) to Group"
5. The group will appear in the "Playback Target" dropdown

### Mixed Device Groups

You can create groups that include both Chromecast devices and web clients:

1. Register your web clients (laptops, phones, tablets)
2. Discover your Chromecast devices on the network
3. Create a group and add both types of devices
4. Select the group as your playback target
5. Control playback for all devices from a single interface

## Project Structure

```
chromecast_web_playlist/
├── core/                 # Core functionality
│   ├── playlist_manager.py  # Playlist management
│   ├── device_manager.py    # Device and group management
│   ├── media_player.py      # Playback functionality
│   └── chromecast_manager.py # Main interface
├── extractors/           # Media extraction
│   ├── web_scraper.py       # Web page scraping
│   ├── x_extractor.py       # X/Twitter extraction
│   └── media_extractor.py   # Unified extraction
├── web/                  # Web interface
│   ├── server.py            # Flask server
│   ├── api.py               # API endpoints
│   ├── templates/           # HTML templates
│   └── static/              # Static files
├── cli/                  # Command-line interface
│   └── commands.py          # CLI commands
└── utils/                # Utilities
    └── helpers.py           # Helper functions
```

## Dependencies

- Python 3.11+
- pychromecast: Chromecast device discovery and control
- Flask & Flask-SocketIO: Web server and real-time updates
- Playwright: Web scraping and media extraction
- Requests: HTTP client for API calls
- Zeroconf: Service discovery

## License

MIT
