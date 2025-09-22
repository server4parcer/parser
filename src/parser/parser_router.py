"""
Parser Router - Routes URLs to appropriate parser based on content type.
"""
import asyncio
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse

from src.parser.lightweight_yclients_parser import LightweightYClientsParser
from src.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class ParserRouter:
    """Routes URLs to appropriate parser implementation."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.lightweight_parser = LightweightYClientsParser()
        
    async def parse_url(self, url: str) -> List[Dict]:
        """
        Route URL to appropriate parser.
        YClients → Lightweight YClients parser (requests + BeautifulSoup)
        Others → Generic lightweight parser (fallback)
        """
        # Check if it's a YClients URL
        if self.is_yclients_url(url):
            logger.info(f"🎯 Routing to Lightweight YClients parser: {url}")
            return await self.parse_with_lightweight_yclients(url)
        else:
            logger.info(f"📄 Routing to generic lightweight parser: {url}")
            # For non-YClients URLs, return empty list for now
            # Can be extended to handle other booking platforms
            logger.warning(f"Non-YClients URL detected: {url} - returning empty results")
            return []
    
    def is_yclients_url(self, url: str) -> bool:
        """Check if URL is YClients booking page."""
        yclients_indicators = [
            'yclients.com',
            'record-type',
            'personal/',
            'select-time',
            'select-master',
            'select-services',
            'personal/menu'
        ]
        return any(indicator in url for indicator in yclients_indicators)
    
    async def parse_with_lightweight_yclients(self, url: str) -> List[Dict]:
        """Parse using lightweight YClients parser (requests + BeautifulSoup)."""
        try:
            logger.info(f"🚀 Using lightweight YClients parser for: {url}")
            # Run in asyncio executor to make it async
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, self.lightweight_parser.parse_url, url)
            logger.info(f"✅ Lightweight parser extracted {len(data)} records from {url}")
            return data
        except Exception as e:
            logger.error(f"❌ Lightweight YClients parsing failed for {url}: {e}")
            return []
    
    async def parse_multiple_urls(self, urls: List[str]) -> Dict[str, List[Dict]]:
        """Parse multiple URLs and return results."""
        results = {}
        
        for url in urls:
            logger.info(f"🔍 Processing URL: {url}")
            try:
                url_results = await self.parse_url(url)
                results[url] = url_results
                logger.info(f"✅ Extracted {len(url_results)} records from {url}")
            except Exception as e:
                logger.error(f"❌ Failed to parse {url}: {e}")
                results[url] = []
        
        return results
    
    async def close(self):
        """Clean up all resources."""
        # Lightweight parser doesn't need cleanup
        pass