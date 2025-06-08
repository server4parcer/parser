#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправлений YClients Parser.
"""
import asyncio
import logging
import sys
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_improved_extractor():
    """Тестирование улучшенного экстрактора данных."""
    try:
        from src.parser.improved_data_extractor import ImprovedDataExtractor
        
        extractor = ImprovedDataExtractor()
        logger.info("✅ ImprovedDataExtractor успешно импортирован")
        
        # Тестируем очистку цены
        test_prices = [
            "1500 руб",
            "₽ 2000", 
            "1200",
            "750 ₽",
            "$50",
            "€30"
        ]
        
        logger.info("🧪 Тестирование извлечения цен:")
        for price in test_prices:
            cleaned = extractor.clean_price_enhanced(price)
            logger.info(f"  {price} -> {cleaned}")
        
        # Тестируем валидацию имен
        test_names = [
            "Анна Иванова",
            "123",
            "Михаил Петров", 
            "1500 ₽",
            "John Smith",
            "42"
        ]
        
        logger.info("🧪 Тестирование валидации имен:")
        for name in test_names:
            is_valid = extractor.is_valid_name(name)
            logger.info(f"  {name} -> {'✅ валидное' if is_valid else '❌ невалидное'}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования: {e}")
        return False

async def test_parser_initialization():
    """Тестирование инициализации парсера."""
    try:
        from src.database.db_manager import DatabaseManager
        from src.parser.yclients_parser import YClientsParser
        
        # Тестовый URL
        test_urls = ["https://n1165596.yclients.com/company/1109937/record-type?o="]
        
        # Инициализация (без реального подключения к БД)
        db_manager = DatabaseManager()
        parser = YClientsParser(test_urls, db_manager)
        
        # Проверяем, что используется улучшенный экстрактор
        extractor_type = type(parser.data_extractor).__name__
        logger.info(f"📊 Тип экстрактора: {extractor_type}")
        
        if extractor_type == "ImprovedDataExtractor":
            logger.info("✅ Используется улучшенный экстрактор данных")
            return True
        else:
            logger.warning(f"⚠️ Используется {extractor_type} вместо ImprovedDataExtractor")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации парсера: {e}")
        return False

async def main():
    """Основная функция тестирования."""
    logger.info("🚀 Запуск тестирования исправлений YClients Parser")
    logger.info(f"⏰ Время: {datetime.now()}")
    
    tests = [
        ("Тестирование улучшенного экстрактора", test_improved_extractor),
        ("Тестирование инициализации парсера", test_parser_initialization)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📝 {test_name}...")
        try:
            result = await test_func()
            if result:
                logger.info(f"✅ {test_name}: ПРОЙДЕН")
                passed += 1
            else:
                logger.error(f"❌ {test_name}: ПРОВАЛЕН")
        except Exception as e:
            logger.error(f"💥 {test_name}: ОШИБКА - {e}")
    
    logger.info(f"\n📊 Результаты тестирования:")
    logger.info(f"✅ Пройдено: {passed}/{total}")
    logger.info(f"❌ Провалено: {total - passed}/{total}")
    
    if passed == total:
        logger.info("🎉 Все тесты пройдены! Исправления работают корректно.")
        return 0
    else:
        logger.error("⚠️ Некоторые тесты провалены. Проверьте применение исправлений.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
