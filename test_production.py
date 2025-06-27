#!/usr/bin/env python3
"""
Простой тест парсера для проверки функциональности
"""
import requests
import json
import time

def test_parser_functionality():
    """Тест основной функциональности парсера"""
    base_url = "https://server4parcer-parser-4949.twc1.net"
    
    print("🧪 ТЕСТИРОВАНИЕ ФУНКЦИОНАЛЬНОСТИ ПАРСЕРА")
    print("=" * 50)
    
    # 1. Проверка здоровья системы
    print("1. Проверка /health...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Система здорова: {health_data.get('message')}")
            print(f"   📊 URL настроено: {health_data.get('parser', {}).get('urls_configured', 0)}")
        else:
            print(f"   ❌ Ошибка health check: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")
        return False
    
    # 2. Проверка статуса парсера
    print("\n2. Проверка /parser/status...")
    try:
        response = requests.get(f"{base_url}/parser/status", timeout=10)
        if response.status_code == 200:
            status_data = response.json()
            print(f"   ✅ Статус парсера: {status_data.get('status')}")
            print(f"   🔧 Готовность: {status_data.get('ready')}")
            urls = status_data.get('configuration', {}).get('urls', [])
            print(f"   📋 URL для парсинга: {len(urls)}")
            for i, url in enumerate(urls, 1):
                print(f"      {i}. {url[:60]}...")
        else:
            print(f"   ❌ Ошибка получения статуса: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # 3. Запуск парсера
    print("\n3. Запуск парсера /parser/run...")
    try:
        response = requests.post(f"{base_url}/parser/run", timeout=60)
        if response.status_code == 200:
            run_result = response.json()
            print(f"   📊 Результат запуска: {run_result.get('status')}")
            
            if run_result.get('status') == 'success':
                extracted = run_result.get('extracted', 0)
                print(f"   🎉 Успешно извлечено: {extracted} записей!")
                return True
            elif run_result.get('status') == 'error':
                error_msg = run_result.get('message', 'Неизвестная ошибка')
                print(f"   ❌ Ошибка парсинга: {error_msg}")
                if 'Executable doesn\'t exist' in error_msg:
                    print("   🔧 Проблема с установкой Playwright браузеров")
                return False
            else:
                print(f"   ⚠️ Неожиданный статус: {run_result}")
                return False
        else:
            print(f"   ❌ Ошибка запуска парсера: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    # 4. Проверка извлеченных данных
    print("\n4. Проверка /api/booking-data...")
    try:
        response = requests.get(f"{base_url}/api/booking-data", timeout=10)
        if response.status_code == 200:
            data_result = response.json()
            total_records = data_result.get('total', 0)
            print(f"   📊 Всего записей в базе: {total_records}")
            
            if total_records > 0:
                sample_data = data_result.get('data', [])
                if sample_data:
                    sample = sample_data[0]
                    print(f"   📝 Пример данных:")
                    print(f"      Дата: {sample.get('date')}")
                    print(f"      Время: {sample.get('time')}")
                    print(f"      Цена: {sample.get('price')}")
                    print(f"      Провайдер: {sample.get('provider')}")
                    return True
            else:
                print("   ℹ️ Данные пока не извлечены")
                return False
        else:
            print(f"   ❌ Ошибка получения данных: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_parser_functionality()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Парсер работает корректно.")
    else:
        print("❌ ТЕСТЫ НЕ ПРОЙДЕНЫ. Требуется дальнейшая отладка.")
    print("=" * 50)
