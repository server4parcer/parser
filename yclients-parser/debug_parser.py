#!/usr/bin/env python3
"""
Debug script to test YClients parser locally and identify the parsing issues.
"""
import asyncio
import logging
import os
import sys
from playwright.async_api import async_playwright

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.parser.improved_data_extractor import ImprovedDataExtractor
from src.parser.selectors import is_time_not_price, is_price_not_time, is_valid_provider_name

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_yclients_page():
    """Debug the YClients page to understand its structure."""
    url = "https://n1165596.yclients.com/company/1109937/record-type?o="
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            logger.info(f"🔍 Loading page: {url}")
            await page.goto(url, wait_until='networkidle')
            await asyncio.sleep(3)  # Wait for dynamic content
            
            # Get page title and basic info
            title = await page.title()
            current_url = page.url
            logger.info(f"📄 Page title: {title}")
            logger.info(f"🔗 Current URL: {current_url}")
            
            # Check if redirected
            if current_url != url:
                logger.warning(f"⚠️ Redirected from {url} to {current_url}")
            
            # Look for common booking elements
            await debug_elements(page)
            
            # Look for service selection elements
            await debug_service_selection(page)
            
            # Look for calendar/date elements
            await debug_calendar_elements(page)
            
            # Get page HTML for manual inspection
            html_content = await page.content()
            
            # Save HTML for analysis
            with open('debug_page_content.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info("💾 Page content saved to debug_page_content.html")
            
        except Exception as e:
            logger.error(f"❌ Error during debugging: {str(e)}")
        
        finally:
            await browser.close()

async def debug_elements(page):
    """Debug specific elements on the page."""
    logger.info("🔍 Debugging page elements...")
    
    # Common selectors to check
    selectors_to_check = [
        '.service-item',
        '.service-option', 
        '.record__service',
        '.ycwidget-service',
        '.booking-service-item',
        '.time-slot',
        '.slot-item',
        '.time-item',
        '.booking-time-slot',
        '.price',
        '.cost',
        '.amount',
        '.service-price',
        '.booking-price',
        '.price-value',
        '.staff-name',
        '.provider-name',
        '.specialist-name',
        '.master-name',
        '.employee-name'
    ]
    
    for selector in selectors_to_check:
        try:
            elements = await page.query_selector_all(selector)
            if elements:
                logger.info(f"✅ Found {len(elements)} elements for selector: {selector}")
                
                # Get text content from first few elements
                for i, element in enumerate(elements[:3]):
                    text = await element.text_content()
                    if text and text.strip():
                        logger.info(f"   [{i+1}] Text: {text.strip()[:100]}")
        except Exception as e:
            logger.debug(f"❌ Error checking selector {selector}: {str(e)}")

async def debug_service_selection(page):
    """Debug service selection elements."""
    logger.info("🔍 Debugging service selection...")
    
    # Look for service selection elements
    service_selectors = [
        'a[href*="record"]',
        'button[onclick*="record"]',
        '.service-link',
        '.booking-link',
        '[data-service-id]',
        '[data-service]'
    ]
    
    for selector in service_selectors:
        try:
            elements = await page.query_selector_all(selector)
            if elements:
                logger.info(f"🔗 Found {len(elements)} service links for: {selector}")
                
                for i, element in enumerate(elements[:3]):
                    href = await element.get_attribute('href')
                    text = await element.text_content()
                    if href:
                        logger.info(f"   Link {i+1}: {href} | Text: {text.strip()[:50] if text else 'No text'}")
        except Exception as e:
            logger.debug(f"❌ Error checking service selector {selector}: {str(e)}")

async def debug_calendar_elements(page):
    """Debug calendar and date elements."""
    logger.info("🔍 Debugging calendar elements...")
    
    calendar_selectors = [
        '.calendar',
        '.booking-calendar',
        '.rc-calendar',
        '.date-picker',
        '[data-date]',
        '.available-day',
        '.selectable-date'
    ]
    
    for selector in calendar_selectors:
        try:
            elements = await page.query_selector_all(selector)
            if elements:
                logger.info(f"📅 Found {len(elements)} calendar elements for: {selector}")
        except Exception as e:
            logger.debug(f"❌ Error checking calendar selector {selector}: {str(e)}")

async def test_validation_functions():
    """Test the validation functions with sample data."""
    logger.info("🧪 Testing validation functions...")
    
    test_cases = [
        # Time values (should NOT be prices)
        ("22:00", "time"),
        ("07:30", "time"), 
        ("14:15", "time"),
        ("23:59", "time"),
        
        # Price values (should be prices)
        ("1500₽", "price"),
        ("2000 руб", "price"),
        ("500 рублей", "price"),
        ("1200", "price_maybe"),
        
        # Names (should be valid names)
        ("Анна Иванова", "name"),
        ("John Smith", "name"),
        ("Мария", "name"),
        ("Не указан", "not_name"),
        ("22", "not_name"),
        
        # Mixed cases
        ("22₽", "suspicious"),  # This is what we're seeing in DB
        ("7₽", "suspicious"),
        ("8₽", "suspicious"),
    ]
    
    for value, expected_type in test_cases:
        is_time = is_time_not_price(value)
        is_price = is_price_not_time(value) 
        is_name = is_valid_provider_name(value)
        
        logger.info(f"Value: '{value}' | Expected: {expected_type}")
        logger.info(f"  is_time_not_price: {is_time}")
        logger.info(f"  is_price_not_time: {is_price}")
        logger.info(f"  is_valid_provider_name: {is_name}")
        
        # Check if our suspicious cases are being misclassified
        if expected_type == "suspicious":
            if is_price and not is_time:
                logger.warning(f"⚠️ '{value}' is being classified as PRICE - this might be the bug!")
        
        logger.info("")

if __name__ == "__main__":
    try:
        logger.info("🚀 Starting YClients parser debug...")
        
        # Test validation functions first
        asyncio.run(test_validation_functions())
        
        # Then debug the actual website
        asyncio.run(debug_yclients_page())
        
    except KeyboardInterrupt:
        logger.info("⛔ Debug stopped by user")
    except Exception as e:
        logger.error(f"💥 Error during debug: {str(e)}")
