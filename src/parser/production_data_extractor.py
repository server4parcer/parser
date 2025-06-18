"""
Production-ready data extractor with real YClients selectors.
Final version for Timeweb deployment.
"""
import asyncio
import logging
import re
from datetime import datetime, time
from typing import Dict, List, Optional, Any

from playwright.async_api import ElementHandle, Page
from src.parser.yclients_real_selectors import (
    YCLIENTS_REAL_SELECTORS, 
    YCLIENTS_COMBINED_SELECTORS,
    YCLIENTS_XPATH_SELECTORS,
    get_safe_price_selector,
    get_safe_time_selector,
    get_safe_provider_selector,
    is_valid_yclients_price,
    is_valid_yclients_provider
)

logger = logging.getLogger(__name__)


class ProductionDataExtractor:
    """
    Production-ready data extractor for YClients.
    Uses real website selectors and robust validation.
    """

    def __init__(self):
        """Initialize the extractor with real YClients selectors."""
        self.selectors = YCLIENTS_REAL_SELECTORS
        self.safe_selectors = YCLIENTS_COMBINED_SELECTORS
        self.xpath_selectors = YCLIENTS_XPATH_SELECTORS
        
        # Compile regex patterns for performance
        self.time_pattern = re.compile(r'^\d{1,2}:\d{2}(:\d{2})?$')
        self.hour_pattern = re.compile(r'^([01]?\d|2[0-3])$')

    async def extract_text_safely(self, element: ElementHandle) -> str:
        """Safely extract text content from element."""
        try:
            text = await element.text_content()
            return text.strip() if text else ""
        except Exception as e:
            logger.debug(f"Error extracting text: {e}")
            return ""

    async def extract_attribute_safely(self, element: ElementHandle, attr: str) -> str:
        """Safely extract attribute from element."""
        try:
            value = await element.get_attribute(attr)
            return value.strip() if value else ""
        except Exception as e:
            logger.debug(f"Error extracting attribute {attr}: {e}")
            return ""

    async def find_price_in_slot(self, slot_element: ElementHandle) -> Optional[str]:
        """
        Find price in slot using safe selectors and validation.
        """
        logger.debug("🔍 Searching for price with safe selectors...")
        
        try:
            # 1. Use safe price selectors that avoid time elements
            for price_selector in self.selectors["time_slots"]["price_elements"]:
                try:
                    price_elements = await slot_element.query_selector_all(price_selector)
                    for price_element in price_elements:
                        price_text = await self.extract_text_safely(price_element)
                        if price_text and is_valid_yclients_price(price_text):
                            logger.info(f"✅ Found valid price: {price_text}")
                            return price_text
                except Exception as e:
                    logger.debug(f"Price selector {price_selector} failed: {e}")
                    continue
            
            # 2. Check data attributes (price-specific)
            price_attrs = ['data-price', 'data-cost', 'data-amount']
            for attr in price_attrs:
                # Skip if element has time-related attributes
                if await slot_element.get_attribute('data-time'):
                    continue
                    
                price_value = await self.extract_attribute_safely(slot_element, attr)
                if price_value and is_valid_yclients_price(price_value):
                    logger.info(f"✅ Found price in attribute {attr}: {price_value}")
                    return price_value
            
            # 3. Use XPath for complex searches
            try:
                for xpath in self.xpath_selectors["price_no_time"]:
                    price_texts = await slot_element.evaluate(f"""
                        el => {{
                            const result = document.evaluate('{xpath}', el, null, 
                                XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                            const texts = [];
                            for(let i = 0; i < result.snapshotLength; i++) {{
                                texts.push(result.snapshotItem(i).textContent.trim());
                            }}
                            return texts;
                        }}
                    """)
                    
                    for price_text in price_texts:
                        if price_text and is_valid_yclients_price(price_text):
                            logger.info(f"✅ Found price via XPath: {price_text}")
                            return price_text
            except Exception as e:
                logger.debug(f"XPath price search failed: {e}")
            
            # 4. Last resort: carefully parse element text
            full_text = await self.extract_text_safely(slot_element)
            if full_text:
                # Look for price patterns in text parts
                parts = re.split(r'[\s\n\t]+', full_text)
                for part in parts:
                    if part and is_valid_yclients_price(part):
                        # Double-check it's not a time value
                        if not self.time_pattern.match(part) and not self.looks_like_hour(part):
                            logger.info(f"✅ Found price in text: {part}")
                            return part
            
            logger.debug("❌ No valid price found")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error finding price: {e}")
            return None

    async def find_time_in_slot(self, slot_element: ElementHandle) -> Optional[str]:
        """
        Find time in slot using time-specific selectors.
        """
        logger.debug("🔍 Searching for time...")
        
        try:
            # 1. Use time-specific selectors
            for time_selector in self.selectors["time_slots"]["time_elements"]:
                try:
                    time_element = await slot_element.query_selector(time_selector)
                    if time_element:
                        time_text = await self.extract_text_safely(time_element)
                        if time_text and self.time_pattern.match(time_text):
                            parsed_time = self.parse_time_safely(time_text)
                            if parsed_time:
                                logger.info(f"✅ Found time: {parsed_time}")
                                return parsed_time
                except Exception as e:
                    logger.debug(f"Time selector {time_selector} failed: {e}")
                    continue
            
            # 2. Check data-time attribute
            time_attr = await self.extract_attribute_safely(slot_element, 'data-time')
            if time_attr and self.time_pattern.match(time_attr):
                parsed_time = self.parse_time_safely(time_attr)
                if parsed_time:
                    logger.info(f"✅ Found time in attribute: {parsed_time}")
                    return parsed_time
            
            # 3. XPath search for time patterns
            try:
                for xpath in self.xpath_selectors["time_no_price"]:
                    time_texts = await slot_element.evaluate(f"""
                        el => {{
                            const result = document.evaluate('{xpath}', el, null,
                                XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                            const texts = [];
                            for(let i = 0; i < result.snapshotLength; i++) {{
                                texts.push(result.snapshotItem(i).textContent.trim());
                            }}
                            return texts;
                        }}
                    """)
                    
                    for time_text in time_texts:
                        if time_text and self.time_pattern.match(time_text):
                            parsed_time = self.parse_time_safely(time_text)
                            if parsed_time:
                                logger.info(f"✅ Found time via XPath: {parsed_time}")
                                return parsed_time
            except Exception as e:
                logger.debug(f"XPath time search failed: {e}")
            
            # 4. Search in element text for time patterns
            full_text = await self.extract_text_safely(slot_element)
            if full_text:
                time_matches = self.time_pattern.findall(full_text)
                for time_match in time_matches:
                    parsed_time = self.parse_time_safely(time_match)
                    if parsed_time:
                        logger.info(f"✅ Found time in text: {parsed_time}")
                        return parsed_time
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error finding time: {e}")
            return None

    async def find_provider_in_slot(self, slot_element: ElementHandle) -> str:
        """
        Find provider/staff name in slot.
        """
        logger.debug("🔍 Searching for provider...")
        
        try:
            # 1. Use provider-specific selectors
            for provider_selector in self.selectors["time_slots"]["provider_elements"]:
                try:
                    provider_elements = await slot_element.query_selector_all(provider_selector)
                    for provider_element in provider_elements:
                        provider_text = await self.extract_text_safely(provider_element)
                        if provider_text and is_valid_yclients_provider(provider_text):
                            logger.info(f"✅ Found provider: {provider_text}")
                            return provider_text.strip()
                except Exception as e:
                    logger.debug(f"Provider selector {provider_selector} failed: {e}")
                    continue
            
            # 2. Check staff-related attributes
            staff_attrs = ['data-staff-name', 'data-staff', 'data-specialist', 'data-master']
            for attr in staff_attrs:
                provider_value = await self.extract_attribute_safely(slot_element, attr)
                if provider_value and is_valid_yclients_provider(provider_value):
                    logger.info(f"✅ Found provider in attribute {attr}: {provider_value}")
                    return provider_value.strip()
            
            # 3. XPath search for provider names
            try:
                for xpath in self.xpath_selectors["provider_names"]:
                    provider_texts = await slot_element.evaluate(f"""
                        el => {{
                            const result = document.evaluate('{xpath}', el, null,
                                XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                            const texts = [];
                            for(let i = 0; i < result.snapshotLength; i++) {{
                                texts.push(result.snapshotItem(i).textContent.trim());
                            }}
                            return texts;
                        }}
                    """)
                    
                    for provider_text in provider_texts:
                        if provider_text and is_valid_yclients_provider(provider_text):
                            logger.info(f"✅ Found provider via XPath: {provider_text}")
                            return provider_text.strip()
            except Exception as e:
                logger.debug(f"XPath provider search failed: {e}")
            
            logger.debug("❌ No valid provider found")
            return "Не указан"
            
        except Exception as e:
            logger.error(f"❌ Error finding provider: {e}")
            return "Не указан"

    def looks_like_hour(self, text: str) -> bool:
        """Check if text looks like an hour value (0-23)."""
        try:
            # Remove currency symbols and check if it's 0-23
            clean_text = re.sub(r'[₽$€руб]', '', text).strip()
            num = int(clean_text)
            return 0 <= num <= 23
        except ValueError:
            return False

    def parse_time_safely(self, time_str: str) -> Optional[str]:
        """Safely parse time string to ISO format."""
        try:
            if self.time_pattern.match(time_str):
                if ':' in time_str:
                    parts = time_str.split(':')
                    if len(parts) >= 2:
                        hour, minute = int(parts[0]), int(parts[1])
                        if 0 <= hour <= 23 and 0 <= minute <= 59:
                            return f"{hour:02d}:{minute:02d}:00"
            return None
        except Exception:
            return None

    async def extract_slot_data_production(self, slot_element: ElementHandle) -> Dict[str, Any]:
        """
        Extract all slot data using production-ready methods.
        """
        logger.debug("📊 Extracting slot data (production method)...")
        
        try:
            result = {}
            
            # Extract time first (highest priority)
            time_value = await self.find_time_in_slot(slot_element)
            if time_value:
                result['time'] = time_value
            
            # Extract price (with strict validation)
            price_value = await self.find_price_in_slot(slot_element)
            result['price'] = price_value if price_value else "Цена не найдена"
            
            # Extract provider
            provider_value = await self.find_provider_in_slot(slot_element)
            result['provider'] = provider_value
            
            # Add metadata
            result['extracted_at'] = datetime.now().isoformat()
            
            logger.info(f"📊 Extracted data: time={result.get('time', 'нет')}, price={result.get('price')}, provider={result.get('provider')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error extracting slot data: {e}")
            return {}

    # Alias for backwards compatibility with the main parser
    async def extract_slot_data_fixed(self, slot_element: ElementHandle) -> Dict[str, Any]:
        """Alias for production method to maintain compatibility."""
        return await self.extract_slot_data_production(slot_element)
