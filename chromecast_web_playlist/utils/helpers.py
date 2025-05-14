#!/usr/bin/env python3
"""
Helper Utilities
Common utility functions for the Chromecast Web Playlist Manager
"""

import os
import re
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse, urljoin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_url(url: str) -> bool:
    """
    Check if a string is a valid URL.
    
    Args:
        url: String to check
        
    Returns:
        True if the string is a valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False
        
def is_media_url(url: str) -> bool:
    """
    Check if a URL is a media URL based on its extension.
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is a media URL, False otherwise
    """
    if not is_url(url):
        return False
        
    # Check if the URL has a file extension
    path = urlparse(url).path.lower()
    media_extensions = [
        ".mp4", ".webm", ".ogg", ".mp3", ".wav", ".m4a", ".m4v", ".mov",
        ".avi", ".wmv", ".flv", ".mkv", ".m3u8", ".mpd"
    ]
    
    return any(path.endswith(ext) for ext in media_extensions)
    
def format_time(seconds: float) -> str:
    """
    Format time in seconds to a human-readable string.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string (HH:MM:SS)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"
        
def format_size(size_bytes: int) -> str:
    """
    Format size in bytes to a human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.23 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
        
def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Replace invalid characters with underscores
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. ')
    
    # Limit length
    if len(sanitized) > 255:
        base, ext = os.path.splitext(sanitized)
        sanitized = base[:255 - len(ext)] + ext
        
    return sanitized or 'unnamed'
    
def load_json(file_path: str, default: Any = None) -> Any:
    """
    Load JSON data from a file.
    
    Args:
        file_path: Path to the JSON file
        default: Default value to return if the file doesn't exist or is invalid
        
    Returns:
        Loaded JSON data or default value
    """
    if not os.path.exists(file_path):
        return default
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return default
        
def save_json(file_path: str, data: Any) -> bool:
    """
    Save JSON data to a file.
    
    Args:
        file_path: Path to the JSON file
        data: Data to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except IOError as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        return False
        
def retry(func, retries: int = 3, delay: float = 1.0, backoff: float = 2.0, 
         exceptions: tuple = (Exception,)):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        retries: Number of retries
        delay: Initial delay between retries
        backoff: Backoff multiplier
        exceptions: Exceptions to catch
        
    Returns:
        Result of the function
    """
    for i in range(retries):
        try:
            return func()
        except exceptions as e:
            if i == retries - 1:
                raise
            wait = delay * (backoff ** i)
            logger.warning(f"Retry {i+1}/{retries} after {wait:.2f}s due to: {e}")
            time.sleep(wait)
