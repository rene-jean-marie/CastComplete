#!/usr/bin/env python3
"""
X (Twitter) Video Extractor
Extract videos from X (Twitter) posts using Playwright
"""

import re
import json
import os
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from urllib.parse import urlparse

# Try to import Playwright
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XExtractor:
    """
    Extract videos from X (Twitter) posts using Playwright.
    """
    
    def __init__(self):
        """Initialize the XExtractor."""
        self.playwright = None
        self.browser = None
        
    def _ensure_browser(self):
        """Ensure that the browser is initialized."""
        if not HAS_PLAYWRIGHT:
            raise ImportError("Playwright is required for X extraction. Install with: pip install playwright")
            
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
            
    def extract_video_from_post(self, url: str) -> Dict[str, Any]:
        """
        Extract video from an X (Twitter) post.
        
        Args:
            url: URL of the X post
            
        Returns:
            Dictionary with extracted video information
        """
        try:
            self._ensure_browser()
            
            # Create a new page
            page = self.browser.new_page()
            
            # Navigate to the URL
            logger.info(f"Navigating to {url}")
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Extract post information
            title = page.title()
            
            # Extract video URLs
            video_urls = []
            
            # Wait for video elements to load
            page.wait_for_selector("video", timeout=10000, state="attached")
            
            # Extract video elements
            video_elements = page.query_selector_all("video")
            for video in video_elements:
                src = video.get_attribute("src")
                if src:
                    video_urls.append({
                        "url": src,
                        "type": "video",
                        "source": "video_element"
                    })
                    
            # Extract video URLs from network requests
            requests = []
            page.on("request", lambda request: requests.append(request.url))
            
            # Wait a bit more for any delayed requests
            page.wait_for_timeout(2000)
            
            # Check for video URLs in requests
            for req_url in requests:
                if "video" in req_url and req_url.endswith((".mp4", ".m3u8")):
                    video_urls.append({
                        "url": req_url,
                        "type": "video",
                        "source": "network_request"
                    })
                    
            # Extract video URLs from JavaScript
            js_video_urls = page.evaluate("""() => {
                const results = [];
                
                // Look for video URLs in the page
                const videoElements = document.querySelectorAll('video');
                for (const video of videoElements) {
                    if (video.src) {
                        results.push({
                            url: video.src,
                            type: 'video',
                            source: 'js_video_element'
                        });
                    }
                    
                    // Check for source elements
                    const sources = video.querySelectorAll('source');
                    for (const source of sources) {
                        if (source.src) {
                            results.push({
                                url: source.src,
                                type: 'video',
                                source: 'js_source_element'
                            });
                        }
                    }
                }
                
                // Look for video URLs in the page content
                const content = document.documentElement.outerHTML;
                const videoUrlMatches = content.match(/https?:\\/\\/[^\\s"']+\\.(?:mp4|m3u8)[^\\s"']*/g);
                if (videoUrlMatches) {
                    for (const url of videoUrlMatches) {
                        results.push({
                            url: url,
                            type: 'video',
                            source: 'js_regex'
                        });
                    }
                }
                
                return results;
            }""")
            
            # Add JavaScript-extracted URLs
            for item in js_video_urls:
                video_urls.append(item)
                
            # Close the page
            page.close()
            
            # Remove duplicates
            unique_urls = []
            seen_urls = set()
            for item in video_urls:
                if item["url"] not in seen_urls:
                    seen_urls.add(item["url"])
                    unique_urls.append(item)
                    
            # Extract post text
            post_text = title.split(" on X:")[0] if " on X:" in title else title
            
            return {
                "title": post_text,
                "url": url,
                "video_urls": unique_urls
            }
            
        except Exception as e:
            logger.error(f"Error extracting video from X post {url}: {str(e)}")
            return {
                "title": url,
                "url": url,
                "video_urls": [],
                "error": str(e)
            }
            
    def extract_videos_from_feed(self, url: str, scroll_count: int = 5) -> List[Dict[str, Any]]:
        """
        Extract videos from an X feed by scrolling through it.
        
        Args:
            url: URL of the X feed
            scroll_count: Number of times to scroll the feed
            
        Returns:
            List of dictionaries with extracted video information
        """
        try:
            self._ensure_browser()
            
            # Create a new page
            page = self.browser.new_page()
            
            # Navigate to the URL
            logger.info(f"Navigating to {url}")
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Extract feed information
            title = page.title()
            
            # Extract video posts
            video_posts = []
            
            # Scroll through the feed
            for i in range(scroll_count):
                logger.info(f"Scrolling feed ({i+1}/{scroll_count})")
                
                # Wait for posts to load
                page.wait_for_selector("article", timeout=10000, state="attached")
                
                # Extract posts with videos
                posts = page.query_selector_all("article")
                
                for post in posts:
                    # Check if the post has a video
                    video = post.query_selector("video")
                    if not video:
                        continue
                        
                    # Extract post URL
                    link = post.query_selector("a[href*='/status/']")
                    if not link:
                        continue
                        
                    post_url = link.get_attribute("href")
                    if not post_url.startswith("http"):
                        post_url = f"https://twitter.com{post_url}"
                        
                    # Extract post text
                    text_element = post.query_selector("[data-testid='tweetText']")
                    post_text = text_element.inner_text() if text_element else ""
                    
                    # Extract video URL
                    video_url = video.get_attribute("src")
                    
                    # Add to results
                    if post_url and video_url:
                        video_posts.append({
                            "title": post_text or f"X Post {len(video_posts) + 1}",
                            "url": post_url,
                            "video_urls": [{
                                "url": video_url,
                                "type": "video",
                                "source": "feed_video_element"
                            }]
                        })
                        
                # Scroll down
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)  # Wait for new content to load
                
            # Close the page
            page.close()
            
            # Remove duplicates
            unique_posts = []
            seen_urls = set()
            for post in video_posts:
                if post["url"] not in seen_urls:
                    seen_urls.add(post["url"])
                    unique_posts.append(post)
                    
            return unique_posts
            
        except Exception as e:
            logger.error(f"Error extracting videos from X feed {url}: {str(e)}")
            return []
            
# Singleton instance for convenience
_extractor = None

def get_extractor() -> XExtractor:
    """Get a singleton instance of the XExtractor."""
    global _extractor
    if _extractor is None:
        _extractor = XExtractor()
    return _extractor
    
def extract_video_from_post(url: str) -> Dict[str, Any]:
    """
    Extract video from an X (Twitter) post.
    
    Args:
        url: URL of the X post
        
    Returns:
        Dictionary with extracted video information
    """
    extractor = get_extractor()
    return extractor.extract_video_from_post(url)
    
def extract_videos_from_feed(url: str, scroll_count: int = 5) -> List[Dict[str, Any]]:
    """
    Extract videos from an X feed by scrolling through it.
    
    Args:
        url: URL of the X feed
        scroll_count: Number of times to scroll the feed
        
    Returns:
        List of dictionaries with extracted video information
    """
    extractor = get_extractor()
    return extractor.extract_videos_from_feed(url, scroll_count)
    
def close_extractor():
    """Close the singleton extractor instance."""
    global _extractor
    if _extractor:
        _extractor.close()
        _extractor = None
