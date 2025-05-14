#!/usr/bin/env python3
"""
Media Extractor
Unified interface for extracting media from various sources
"""

import re
import logging
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse

from .web_scraper import extract_media_from_url, validate_media_url
from .x_extractor import extract_video_from_post, extract_videos_from_feed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_x_url(url: str) -> bool:
    """
    Check if a URL is from X (Twitter).
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is from X, False otherwise
    """
    parsed_url = urlparse(url)
    return parsed_url.netloc in ["twitter.com", "x.com", "www.twitter.com", "www.x.com"]
    
def is_x_post_url(url: str) -> bool:
    """
    Check if a URL is an X post.
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is an X post, False otherwise
    """
    if not is_x_url(url):
        return False
        
    # Check if the URL contains /status/ which indicates a post
    return "/status/" in url
    
def is_x_feed_url(url: str) -> bool:
    """
    Check if a URL is an X feed.
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is an X feed, False otherwise
    """
    if not is_x_url(url):
        return False
        
    # Check if the URL does not contain /status/ which indicates a feed
    return "/status/" not in url
    
def extract_media(url: str) -> Dict[str, Any]:
    """
    Extract media from a URL, detecting the appropriate extractor.
    
    Args:
        url: URL to extract media from
        
    Returns:
        Dictionary with extracted media information
    """
    try:
        # Check if the URL is a direct media URL
        if validate_media_url(url):
            return {
                "title": url.split("/")[-1],
                "url": url,
                "media_urls": [{
                    "url": url,
                    "type": "direct",
                    "source": "direct_url"
                }]
            }
            
        # Check if the URL is from X
        if is_x_post_url(url):
            logger.info(f"Extracting X post: {url}")
            result = extract_video_from_post(url)
            
            # Convert video_urls to media_urls for consistency
            if "video_urls" in result:
                result["media_urls"] = result.pop("video_urls")
                
            return result
            
        # For other URLs, use the web scraper
        logger.info(f"Extracting media from web page: {url}")
        return extract_media_from_url(url)
        
    except Exception as e:
        logger.error(f"Error extracting media from {url}: {str(e)}")
        return {
            "title": url,
            "url": url,
            "media_urls": [],
            "error": str(e)
        }
        
def extract_media_batch(urls: List[str]) -> List[Dict[str, Any]]:
    """
    Extract media from multiple URLs.
    
    Args:
        urls: List of URLs to extract media from
        
    Returns:
        List of dictionaries with extracted media information
    """
    results = []
    for url in urls:
        results.append(extract_media(url))
    return results
    
def extract_x_feed(url: str, scroll_count: int = 5) -> List[Dict[str, Any]]:
    """
    Extract videos from an X feed.
    
    Args:
        url: URL of the X feed
        scroll_count: Number of times to scroll the feed
        
    Returns:
        List of dictionaries with extracted video information
    """
    if not is_x_feed_url(url):
        logger.warning(f"URL is not an X feed: {url}")
        return []
        
    logger.info(f"Extracting X feed: {url}")
    results = extract_videos_from_feed(url, scroll_count)
    
    # Convert video_urls to media_urls for consistency
    for result in results:
        if "video_urls" in result:
            result["media_urls"] = result.pop("video_urls")
            
    return results
