# CastComplete Cheatsheet

## Web Interface Quick Reference

### Device Management
- **Discover Devices**: Click the "Discover Devices" button to find Chromecast devices on your network
- **Register Device**: Click "Register This Device" to add your current device (laptop, phone, tablet) as a playback client
- **Unregister Device**: Click "Unregister" to remove your device from the system
- **Connect to Device**: Select a device from the list and click "Connect Selected"
- **Disconnect**: Click "Disconnect" to end the connection with the current device

### Device Groups
- **Create Group**: Enter a name in "New group name" field and click "Create Group"
- **Add to Group**: Select a group, select device(s), click "Add Device(s) to Group"
- **Remove from Group**: Select a group, select device(s), click "Remove Device(s) from Group"
- **Delete Group**: Select a group and click "Delete Group"
- **Refresh Groups**: Click the refresh button (↻) next to "Device Groups"

### Playlist Management
- **Create Playlist**: Enter a name in "New playlist name" field and click "Create"
- **Delete Playlist**: Click the trash icon (🗑️) next to a playlist
- **Play Playlist**: Click the play icon (▶️) next to a playlist
- **View Playlist**: Click on a playlist name to view its contents
- **Refresh Playlists**: Click the refresh button (↻) next to "Playlists"

### Adding Media
- **Add URL**: Enter a URL in the "Media URL" field and click "Add to Playlist"
- **Upload File**: Click "Choose File", select a media file, then click "Upload"
- **Add URL List**: Select "URL List", enter URLs (one per line), select a playlist, click "Upload"

### Playback Controls
- **Play**: Click the play button (▶️)
- **Pause**: Click the pause button (⏸️)
- **Stop**: Click the stop button (⏹️)
- **Previous**: Click the previous button (⏮️)
- **Next**: Click the next button (⏭️)
- **Select Target**: Choose a device or group from the "Playback Target" dropdown

## CLI Quick Reference

### Basic Syntax
```bash
python cli.py [command] [options]
# or using the entry point
castcomplete [command] [options]
```

### Device Commands
```bash
# List devices
python cli.py devices

# Connect to device
python cli.py connect "Living Room TV"

# Disconnect
python cli.py disconnect
```

### Group Commands
```bash
# List groups
python cli.py groups

# Create group
python cli.py create-group "Home Group" "Living Room TV" "Kitchen Speaker"

# Add to group
python cli.py add-to-group "Home Group" "Bedroom TV"

# Remove from group
python cli.py remove-from-group "Home Group" "Kitchen Speaker"

# Delete group
python cli.py delete-group "Home Group"

# Sync group
python cli.py sync-group "Home Group"
```

### Playlist Commands
```bash
# List playlists
python cli.py playlists

# Create playlist
python cli.py create "Weekend Music"

# View playlist
python cli.py view "Weekend Music"

# Add media (direct URL)
python cli.py add "Weekend Music" "https://example.com/music.mp3" --title "My Song"

# Add media (with extraction)
python cli.py add "Weekend Music" "https://youtube.com/watch?v=..." --extract

# Remove item (by index)
python cli.py remove "Weekend Music" 2
```

### Media Extraction
```bash
# Extract media from URL
python cli.py extract "https://example.com/page-with-media"

# Extract and save to playlist
python cli.py extract "https://example.com/page" --save "My Playlist"

# Extract from X (Twitter)
python cli.py extract "https://x.com/username" --scroll 10
```

### Playback Commands
```bash
# Load playlist
python cli.py load "Weekend Music" --device "Living Room TV"
python cli.py load "Weekend Music" --group "Home Group"

# Play
python cli.py play --device "Living Room TV"
python cli.py play --group "Home Group"

# Pause
python cli.py pause --device "Living Room TV"

# Resume
python cli.py resume --device "Living Room TV"

# Stop
python cli.py stop --device "Living Room TV"

# Next/Previous
python cli.py next --device "Living Room TV"
python cli.py prev --device "Living Room TV"
```

### Web Server
```bash
# Start web server
python cli.py server --port 5001 --debug
```

## Keyboard Shortcuts (Web Interface)

- **Space**: Play/Pause
- **N**: Next track
- **P**: Previous track
- **S**: Stop
- **M**: Mute/Unmute
- **↑/↓**: Volume Up/Down
- **F**: Toggle Fullscreen (when video player is active)

## Common Workflows

### Create Multi-Device Experience
1. Register web clients on multiple devices
2. Discover Chromecast devices
3. Create a device group
4. Add both web clients and Chromecast devices to the group
5. Create or select a playlist
6. Select the group as playback target
7. Play the playlist

### Extract and Play Media
1. Find a web page with media (e.g., YouTube video)
2. Create a new playlist
3. Add the URL with extraction enabled
4. Select a playback target
5. Play the playlist

### Upload Local Media
1. Select a target playlist
2. Click "Choose File" and select media file
3. Click "Upload"
4. The file will be uploaded and added to the playlist

### Troubleshooting
- **Device not found**: Click "Discover Devices" to refresh
- **Playback issues**: Try disconnecting and reconnecting to the device
- **Media not playing**: Check if the URL is valid or try extraction
- **Group synchronization issues**: Use the "Sync Group" function
- **Web client not registering**: Refresh the page and try again

## API Endpoints

### Device Management
- `GET /api/devices`: List available devices
- `POST /api/connect`: Connect to a device
- `POST /api/disconnect`: Disconnect from a device

### Web Clients
- `POST /api/web-clients/register`: Register a web client
- `POST /api/web-clients/update`: Update web client status
- `POST /api/web-clients/unregister`: Unregister a web client

### Device Groups
- `GET /api/groups`: List device groups
- `POST /api/groups`: Create a device group
- `DELETE /api/groups/<name>`: Delete a device group
- `POST /api/groups/<name>/add`: Add device to group
- `POST /api/groups/<name>/remove`: Remove device from group
- `POST /api/groups/<name>/sync`: Sync devices in group

### Playlists
- `GET /api/playlists`: List playlists
- `POST /api/playlists`: Create a playlist
- `DELETE /api/playlists/<name>`: Delete a playlist
- `GET /api/playlist/<name>`: Get playlist contents
- `POST /api/playlist/<name>/add`: Add item to playlist
- `POST /api/playlist/<name>/remove`: Remove item from playlist

### Playback
- `POST /api/load`: Load a playlist
- `POST /api/play`: Start playback
- `POST /api/pause`: Pause playback
- `POST /api/resume`: Resume playback
- `POST /api/stop`: Stop playback
- `POST /api/next`: Play next item
- `POST /api/prev`: Play previous item
