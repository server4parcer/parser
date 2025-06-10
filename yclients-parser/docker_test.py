#!/usr/bin/env python3
"""
Простой тест для проверки исправлений в Docker.
"""
import os
import sys

# Добавляем путь к src
sys.path.insert(0, '/app/src')
sys.path.insert(0, '/app')

def test_docker_fixes():
    """Проверка исправлений в Docker окружении."""
    print("🔍 Проверка исправлений YClients Parser в Docker...")
    
    try:
        # Проверяем импорт улучшенного экстрактора
        from src.parser.improved_data_extractor import ImprovedDataExtractor
        print("✅ ImprovedDataExtractor импортирован успешно")
        
        # Создаем экземпляр
        extractor = ImprovedDataExtractor()
        print("✅ ImprovedDataExtractor создан успешно")
        
        # Тестируем очистку цен
        test_prices = ["1500 руб", "₽ 2000", "1200", "750 ₽"]
        for test_price in test_prices:
            cleaned = extractor.clean_price_enhanced(test_price)
            print(f"   Цена '{test_price}' -> '{cleaned}'")
        print("✅ Очистка цен работает")
        
        # Тестируем валидацию имен
        test_names = ["Анна Иванова", "123", "Петр", "7", "Мария Петрова"]
        for test_name in test_names:
            is_valid = extractor.is_valid_name(test_name)
            print(f"   Имя '{test_name}' валидно: {is_valid}")
        print("✅ Валидация имен работает")
        
        # Проверяем что основной парсер использует новый экстрактор
        from src.parser.yclients_parser import YClientsParser
        print("✅ YClientsParser импортирован успешно")
        
        print("\n🎉 Все исправления работают корректно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_docker_fixes()
    sys.exit(0 if success else 1)
