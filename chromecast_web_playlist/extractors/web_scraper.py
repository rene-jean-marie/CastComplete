#!/usr/bin/env python3
"""
Web Scraper Module
Extract media URLs from web pages using Playwright
"""

import re
import json
import os
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from urllib.parse import urlparse, urljoin

# Try to import Playwright
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScraper:
    """
    Extract media URLs from web pages using Playwright.
    """
    
    def __init__(self):
        """Initialize the WebScraper."""
        self.playwright = None
        self.browser = None
        
    def _ensure_browser(self):
        """Ensure that the browser is initialized."""
        if not HAS_PLAYWRIGHT:
            raise ImportError("Playwright is required for web scraping. Install with: pip install playwright")
            
        if not self.playwright:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=True)
            
    def close(self):
        """Close the browser and Playwright."""
        if self.browser:
            self.browser.close()
            self.browser = None
            
        if self.playwright:
            self.playwright.stop()
            self.playwright = None
            
    def extract_media_from_url(self, url: str) -> Dict[str, Any]:
        """
        Extract media URLs from a web page.
        
        Args:
            url: URL of the web page
            
        Returns:
            Dictionary with extracted media information
        """
        try:
            self._ensure_browser()
            
            # Create a new page
            page = self.browser.new_page()
            
            # Navigate to the URL
            logger.info(f"Navigating to {url}")
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Extract page title
            title = page.title()
            
            # Extract media URLs
            media_urls = []
            
            # 1. Look for video elements
            video_elements = page.query_selector_all("video")
            for video in video_elements:
                src = video.get_attribute("src")
                if src:
                    media_urls.append({
                        "url": urljoin(url, src),
                        "type": "video",
                        "source": "video_element"
                    })
                    
                # Check for source elements within video
                source_elements = video.query_selector_all("source")
                for source in source_elements:
                    src = source.get_attribute("src")
                    if src:
                        media_urls.append({
                            "url": urljoin(url, src),
                            "type": "video",
                            "source": "source_element"
                        })
                        
            # 2. Look for audio elements
            audio_elements = page.query_selector_all("audio")
            for audio in audio_elements:
                src = audio.get_attribute("src")
                if src:
                    media_urls.append({
                        "url": urljoin(url, src),
                        "type": "audio",
                        "source": "audio_element"
                    })
                    
                # Check for source elements within audio
                source_elements = audio.query_selector_all("source")
                for source in source_elements:
                    src = source.get_attribute("src")
                    if src:
                        media_urls.append({
                            "url": urljoin(url, src),
                            "type": "audio",
                            "source": "source_element"
                        })
                        
            # 3. Look for HLS/m3u8 streams in network requests
            requests = []
            page.on("request", lambda request: requests.append(request.url))
            
            # Wait a bit more for any delayed requests
            page.wait_for_timeout(2000)
            
            # Check for HLS streams in requests
            for req_url in requests:
                if ".m3u8" in req_url:
                    media_urls.append({
                        "url": req_url,
                        "type": "hls",
                        "source": "network_request"
                    })
                    
            # 4. Execute JavaScript to find media URLs in the page
            js_media_urls = page.evaluate("""() => {
                const results = [];
                
                // Check for video.js players
                if (typeof videojs !== 'undefined') {
                    const players = videojs.getPlayers();
                    for (const playerId in players) {
                        const player = players[playerId];
                        if (player && player.src()) {
                            results.push({
                                url: player.src(),
                                type: 'video',
                                source: 'videojs'
                            });
                        }
                    }
                }
                
                // Check for JW Player
                if (typeof jwplayer !== 'undefined') {
                    const players = jwplayer();
                    if (players) {
                        const config = players.getConfig();
                        if (config && config.file) {
                            results.push({
                                url: config.file,
                                type: 'video',
                                source: 'jwplayer'
                            });
                        }
                    }
                }
                
                return results;
            }""")
            
            # Add JavaScript-extracted URLs
            for item in js_media_urls:
                media_urls.append(item)
                
            # Close the page
            page.close()
            
            # Remove duplicates
            unique_urls = []
            seen_urls = set()
            for item in media_urls:
                if item["url"] not in seen_urls:
                    seen_urls.add(item["url"])
                    unique_urls.append(item)
                    
            return {
                "title": title,
                "url": url,
                "media_urls": unique_urls
            }
            
        except Exception as e:
            logger.error(f"Error extracting media from {url}: {str(e)}")
            return {
                "title": url,
                "url": url,
                "media_urls": [],
                "error": str(e)
            }
            
    def validate_media_url(self, url: str) -> bool:
        """
        Validate if a URL is a valid media URL.
        
        Args:
            url: URL to validate
            
        Returns:
            True if the URL is a valid media URL, False otherwise
        """
        try:
            # Parse the URL
            parsed_url = urlparse(url)
            
            # Check if the URL has a valid scheme
            if not parsed_url.scheme or parsed_url.scheme not in ["http", "https"]:
                return False
                
            # Check if the URL has a valid host
            if not parsed_url.netloc:
                return False
                
            # Check if the URL has a file extension
            path = parsed_url.path.lower()
            media_extensions = [
                ".mp4", ".webm", ".ogg", ".mp3", ".wav", ".m4a", ".m4v", ".mov",
                ".avi", ".wmv", ".flv", ".mkv", ".m3u8", ".mpd"
            ]
            
            if any(path.endswith(ext) for ext in media_extensions):
                return True
                
            # If no file extension, try to fetch headers to check content type
            self._ensure_browser()
            page = self.browser.new_page()
            
            # Create a simple page to test the URL
            page.set_content(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Media Validation</title>
            </head>
            <body>
                <video id="test-video" controls>
                    <source src="{url}" type="video/mp4">
                </video>
                <script>
                    const video = document.getElementById('test-video');
                    video.addEventListener('error', (e) => {{
                        window.mediaError = e.target.error;
                    }});
                    video.addEventListener('loadedmetadata', () => {{
                        window.mediaLoaded = true;
                    }});
                </script>
            </body>
            </html>
            """)
            
            # Wait a bit for the video to load or error
            page.wait_for_timeout(5000)
            
            # Check if the video loaded
            media_loaded = page.evaluate("window.mediaLoaded || false")
            media_error = page.evaluate("window.mediaError ? true : false")
            
            page.close()
            
            return media_loaded and not media_error
            
        except Exception as e:
            logger.error(f"Error validating media URL {url}: {str(e)}")
            return False
            
# Singleton instance for convenience
_scraper = None

def get_scraper() -> WebScraper:
    """Get a singleton instance of the WebScraper."""
    global _scraper
    if _scraper is None:
        _scraper = WebScraper()
    return _scraper
    
def extract_media_from_url(url: str) -> Dict[str, Any]:
    """
    Extract media URLs from a web page.
    
    Args:
        url: URL of the web page
        
    Returns:
        Dictionary with extracted media information
    """
    scraper = get_scraper()
    return scraper.extract_media_from_url(url)
    
def validate_media_url(url: str) -> bool:
    """
    Validate if a URL is a valid media URL.
    
    Args:
        url: URL to validate
        
    Returns:
        True if the URL is a valid media URL, False otherwise
    """
    scraper = get_scraper()
    return scraper.validate_media_url(url)
    
def close_scraper():
    """Close the singleton scraper instance."""
    global _scraper
    if _scraper:
        _scraper.close()
        _scraper = None
