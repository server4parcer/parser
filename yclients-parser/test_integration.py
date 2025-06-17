#!/usr/bin/env python3
"""
Integration test for the fixed parser components.
Tests the database manager's validation and the overall flow.
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.parser.fixed_data_extractor import FixedDataExtractor
from src.database.db_manager import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_integration():
    """Test integration between fixed extractor and database manager."""
    logger.info("🧪 Testing integration...")
    
    # Test data that simulates what the old parser was extracting
    test_data_old_parser = [
        {
            'date': '2025-06-12',
            'time': '22:00:00',
            'price': '22₽',  # This is the bug - time converted to price
            'provider': 'Не указан'
        },
        {
            'date': '2025-06-12', 
            'time': '07:30:00',
            'price': '7₽',  # This is the bug - time converted to price
            'provider': 'Не указан'
        },
        {
            'date': '2025-06-12',
            'time': '14:15:00', 
            'price': '14₽',  # This is the bug - time converted to price
            'provider': 'Не указан'
        }
    ]
    
    # Test data with real prices (what should be extracted)
    test_data_fixed = [
        {
            'date': '2025-06-12',
            'time': '22:00:00',
            'price': '1500₽',  # Real price
            'provider': 'Анна Иванова'
        },
        {
            'date': '2025-06-12',
            'time': '07:30:00', 
            'price': '2000 руб',  # Real price
            'provider': 'Мария Петрова'
        },
        {
            'date': '2025-06-12',
            'time': '14:15:00',
            'price': 'Цена не найдена',  # No price found
            'provider': 'Иван Сидоров'
        }
    ]
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    logger.info("📊 Testing database validation with old buggy data...")
    for i, item in enumerate(test_data_old_parser):
        cleaned = db_manager.clean_booking_data(item)
        logger.info(f"Original #{i+1}: price='{item['price']}' | Cleaned: price='{cleaned['price']}'")
        
        # Check if database manager catches the bug
        if cleaned['price'] == item['price'] and db_manager.is_time_format(item['price']):
            logger.error(f"❌ ERROR: Database manager should have caught time as price: {item['price']}")
        elif cleaned['price'] != item['price']:
            logger.info(f"✅ GOOD: Database manager fixed the price: {item['price']} → {cleaned['price']}")
    
    logger.info("")
    logger.info("📊 Testing database validation with fixed data...")
    for i, item in enumerate(test_data_fixed):
        cleaned = db_manager.clean_booking_data(item)
        logger.info(f"Fixed #{i+1}: price='{item['price']}' | Cleaned: price='{cleaned['price']}'")
        
        # Valid prices should pass through
        if item['price'] in ['1500₽', '2000 руб'] and cleaned['price'] == item['price']:
            logger.info(f"✅ GOOD: Valid price passed through: {item['price']}")
        elif item['price'] == 'Цена не найдена' and cleaned['price'] == item['price']:
            logger.info(f"✅ GOOD: 'Price not found' message preserved")
    
    logger.info("")
    logger.info("🔧 Testing FixedDataExtractor directly...")
    extractor = FixedDataExtractor()
    
    # Test the problematic values
    problematic_values = ['22₽', '7₽', '8₽', '14₽', '22', '7', '8']
    for value in problematic_values:
        cleaned = extractor.clean_price_strict(value)
        if cleaned:
            logger.error(f"❌ ERROR: FixedDataExtractor accepted problematic value: {value} → {cleaned}")
        else:
            logger.info(f"✅ GOOD: FixedDataExtractor rejected problematic value: {value}")

async def test_config_validation():
    """Test configuration and environment setup."""
    logger.info("⚙️ Testing configuration...")
    
    # Check environment variables
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'PARSE_URLS']
    missing_vars = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
        else:
            logger.info(f"✅ {var}: {'*' * min(10, len(value))}...")
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {missing_vars}")
    else:
        logger.info("✅ All required environment variables are set")

if __name__ == "__main__":
    try:
        logger.info("🚀 Starting integration test...")
        
        # Load environment variables from .env
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        except FileNotFoundError:
            logger.warning("⚠️ .env file not found")
        
        # Run tests
        asyncio.run(test_config_validation())
        asyncio.run(test_integration())
        
        logger.info("✅ Integration test completed!")
        
    except Exception as e:
        logger.error(f"💥 Error during integration test: {str(e)}")
