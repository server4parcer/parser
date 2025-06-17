#!/usr/bin/env python3
"""
Test script to verify the fixed data extractor works correctly.
"""
import asyncio
import logging
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.parser.fixed_data_extractor import FixedDataExtractor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_fixed_extractor():
    """Test the fixed data extractor with various scenarios."""
    logger.info("🧪 Testing Fixed Data Extractor...")
    
    extractor = FixedDataExtractor()
    
    # Test cases
    test_cases = [
        # Time values (should NOT be treated as prices)
        ("22:00", "time", False, "Should be time, not price"),
        ("07:30", "time", False, "Should be time, not price"),
        ("14:15", "time", False, "Should be time, not price"),
        
        # Suspicious values that were being misclassified
        ("22₽", "suspicious", False, "Probably hour with added ₽ - should be rejected"),
        ("7₽", "suspicious", False, "Probably hour with added ₽ - should be rejected"),
        ("8₽", "suspicious", False, "Probably hour with added ₽ - should be rejected"),
        
        # Bare numbers (should NOT be treated as prices)
        ("22", "number", False, "Bare number should be rejected"),
        ("7", "number", False, "Bare number should be rejected"),
        ("8", "number", False, "Bare number should be rejected"),
        
        # Valid prices (should be accepted)
        ("1500₽", "price", True, "Valid price with currency"),
        ("2000 руб", "price", True, "Valid price with currency"),
        ("500 рублей", "price", True, "Valid price with currency"),
        
        # Valid names
        ("Анна Иванова", "name", True, "Valid Russian name"),
        ("John Smith", "name", True, "Valid English name"),
        ("Мария", "name", True, "Valid single name"),
        
        # Invalid names
        ("22", "not_name", False, "Number should not be name"),
        ("Не указан", "not_name", False, "Default text should not be valid name"),
    ]
    
    logger.info("=" * 80)
    logger.info("Testing price detection:")
    logger.info("=" * 80)
    
    for value, test_type, should_be_valid, description in test_cases:
        if test_type in ["time", "suspicious", "number", "price"]:
            is_time = extractor.is_definitely_time(value)
            is_price = extractor.is_definitely_price(value)
            is_hour = extractor.is_probably_hour_from_time(value.replace('₽', '').replace('руб', '').strip())
            cleaned_price = extractor.clean_price_strict(value)
            
            logger.info(f"Value: '{value}' | {description}")
            logger.info(f"  is_definitely_time: {is_time}")
            logger.info(f"  is_definitely_price: {is_price}")
            logger.info(f"  is_probably_hour: {is_hour}")
            logger.info(f"  cleaned_price: '{cleaned_price}'")
            
            # Check correctness
            if test_type == "price" and should_be_valid:
                if not cleaned_price:
                    logger.error(f"❌ ERROR: Valid price '{value}' was rejected!")
                else:
                    logger.info(f"✅ CORRECT: Valid price accepted")
            
            elif test_type in ["suspicious", "number"] and not should_be_valid:
                if cleaned_price:
                    logger.error(f"❌ ERROR: Suspicious value '{value}' was accepted as price!")
                else:
                    logger.info(f"✅ CORRECT: Suspicious value rejected")
            
            elif test_type == "time" and not should_be_valid:
                if cleaned_price:
                    logger.error(f"❌ ERROR: Time '{value}' was accepted as price!")
                else:
                    logger.info(f"✅ CORRECT: Time rejected as price")
            
            logger.info("")
    
    logger.info("=" * 80)
    logger.info("Testing name validation:")
    logger.info("=" * 80)
    
    for value, test_type, should_be_valid, description in test_cases:
        if test_type in ["name", "not_name"]:
            is_valid_name = extractor.is_valid_name(value)
            
            logger.info(f"Value: '{value}' | {description}")
            logger.info(f"  is_valid_name: {is_valid_name}")
            
            # Check correctness
            if should_be_valid and not is_valid_name:
                logger.error(f"❌ ERROR: Valid name '{value}' was rejected!")
            elif not should_be_valid and is_valid_name:
                logger.error(f"❌ ERROR: Invalid name '{value}' was accepted!")
            else:
                logger.info(f"✅ CORRECT: Name validation correct")
            
            logger.info("")

if __name__ == "__main__":
    try:
        logger.info("🚀 Starting Fixed Data Extractor test...")
        asyncio.run(test_fixed_extractor())
        logger.info("✅ Test completed!")
        
    except Exception as e:
        logger.error(f"💥 Error during test: {str(e)}")
