"""
Test Export - Модульные тесты для экспорта данных.

Модуль содержит тесты для компонентов экспорта данных.
"""
import json
import os
import tempfile
import unittest
from datetime import datetime

import pytest

from src.export.csv_exporter import CsvExporter
from src.export.json_exporter import JsonExporter
from src.database.models import BookingData, Url


class TestCsvExporter(unittest.TestCase):
    """Тесты для экспортера CSV."""
    
    def setUp(self):
        """Настройка тестов."""
        # Тестовые данные
        self.booking_data = [
            {
                "id": 1,
                "url": "https://example.com",
                "date": "2023-01-01",
                "time": "12:00:00",
                "price": "1000",
                "provider": "Provider 1",
                "seat_number": "1",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            },
            {
                "id": 2,
                "url": "https://example.com",
                "date": "2023-01-02",
                "time": "14:00:00",
                "price": "1500",
                "provider": "Provider 2",
                "seat_number": "2",
                "created_at": "2023-01-02T00:00:00",
                "updated_at": "2023-01-02T00:00:00",
                "additional_field": "Additional value"
            }
        ]
        
        self.urls = [
            {
                "id": 1,
                "url": "https://example1.com",
                "title": "Example 1",
                "description": "Example description 1",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
                "is_active": True
            },
            {
                "id": 2,
                "url": "https://example2.com",
                "title": "Example 2",
                "description": "Example description 2",
                "created_at": "2023-01-02T00:00:00",
                "updated_at": "2023-01-02T00:00:00",
                "is_active": False
            }
        ]
    
    @pytest.mark.asyncio
    async def test_export_booking_data(self):
        """Тест экспорта данных бронирования в CSV."""
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            filepath = temp_file.name
        
        try:
            # Экспортируем данные
            result = await CsvExporter.export_booking_data(filepath, self.booking_data)
            
            # Проверяем, что файл создан
            self.assertTrue(os.path.exists(filepath))
            self.assertEqual(result, filepath)
            
            # Проверяем содержимое файла
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Проверяем заголовки
                self.assertIn("id,url,date,time,price,provider,seat_number", content)
                
                # Проверяем данные
                self.assertIn("1,https://example.com,2023-01-01,12:00:00,1000,Provider 1,1", content)
                self.assertIn("2,https://example.com,2023-01-02,14:00:00,1500,Provider 2,2", content)
                
                # Проверяем дополнительные поля
                self.assertIn("additional_field", content)
                self.assertIn("Additional value", content)
        
        finally:
            # Удаляем временный файл
            if os.path.exists(filepath):
                os.remove(filepath)
    
    @pytest.mark.asyncio
    async def test_export_booking_data_with_models(self):
        """Тест экспорта моделей данных бронирования в CSV."""
        # Создаем модели данных
        booking_data = [
            BookingData(
                id=1,
                url_id=1,
                url="https://example.com",
                date="2023-01-01",
                time="12:00:00",
                price="1000",
                provider="Provider 1",
                seat_number="1",
                created_at=datetime(2023, 1, 1, 0, 0, 0),
                updated_at=datetime(2023, 1, 1, 0, 0, 0)
            ),
            BookingData(
                id=2,
                url_id=1,
                url="https://example.com",
                date="2023-01-02",
                time="14:00:00",
                price="1500",
                provider="Provider 2",
                seat_number="2",
                extra_data={"additional_field": "Additional value"},
                created_at=datetime(2023, 1, 2, 0, 0, 0),
                updated_at=datetime(2023, 1, 2, 0, 0, 0)
            )
        ]
        
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            filepath = temp_file.name
        
        try:
            # Экспортируем данные
            result = await CsvExporter.export_booking_data(filepath, booking_data)
            
            # Проверяем, что файл создан
            self.assertTrue(os.path.exists(filepath))
            self.assertEqual(result, filepath)
            
            # Проверяем содержимое файла
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Проверяем заголовки
                self.assertIn("id,url,date,time,price,provider,seat_number", content)
                
                # Проверяем данные
                self.assertIn("1,https://example.com,2023-01-01,12:00:00,1000,Provider 1,1", content)
                self.assertIn("2,https://example.com,2023-01-02,14:00:00,1500,Provider 2,2", content)
                
                # Проверяем дополнительные поля
                self.assertIn("additional_field", content)
                self.assertIn("Additional value", content)
        
        finally:
            # Удаляем временный файл
            if os.path.exists(filepath):
                os.remove(filepath)
    
    @pytest.mark.asyncio
    async def test_export_urls(self):
        """Тест экспорта URL в CSV."""
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            filepath = temp_file.name
        
        try:
            # Экспортируем данные
            result = await CsvExporter.export_urls(filepath, self.urls)
            
            # Проверяем, что файл создан
            self.assertTrue(os.path.exists(filepath))
            self.assertEqual(result, filepath)
            
            # Проверяем содержимое файла
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Проверяем заголовки
                self.assertIn("id,url,title,description,created_at,updated_at,is_active", content)
                
                # Проверяем данные
                self.assertIn("1,https://example1.com,Example 1,Example description 1", content)
                self.assertIn("2,https://example2.com,Example 2,Example description 2", content)
                
                # Проверяем булевые значения
                self.assertIn("True", content)
                self.assertIn("False", content)
        
        finally:
            # Удаляем временный файл
            if os.path.exists(filepath):
                os.remove(filepath)


class TestJsonExporter(unittest.TestCase):
    """Тесты для экспортера JSON."""
    
    def setUp(self):
        """Настройка тестов."""
        # Тестовые данные
        self.booking_data = [
            {
                "id": 1,
                "url": "https://example.com",
                "date": "2023-01-01",
                "time": "12:00:00",
                "price": "1000",
                "provider": "Provider 1",
                "seat_number": "1",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            },
            {
                "id": 2,
                "url": "https://example.com",
                "date": "2023-01-02",
                "time": "14:00:00",
                "price": "1500",
                "provider": "Provider 2",
                "seat_number": "2",
                "created_at": "2023-01-02T00:00:00",
                "updated_at": "2023-01-02T00:00:00",
                "additional_field": "Additional value"
            }
        ]
        
        self.urls = [
            {
                "id": 1,
                "url": "https://example1.com",
                "title": "Example 1",
                "description": "Example description 1",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
                "is_active": True
            },
            {
                "id": 2,
                "url": "https://example2.com",
                "title": "Example 2",
                "description": "Example description 2",
                "created_at": "2023-01-02T00:00:00",
                "updated_at": "2023-01-02T00:00:00",
                "is_active": False
            }
        ]
        
        self.statistics = {
            "url_count": 2,
            "booking_count": 10,
            "date_stats": [
                {
                    "date": "2023-01-01",
                    "count": 5
                },
                {
                    "date": "2023-01-02",
                    "count": 5
                }
            ],
            "url_stats": [
                {
                    "url": "https://example1.com",
                    "count": 5
                },
                {
                    "url": "https://example2.com",
                    "count": 5
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_export_booking_data(self):
        """Тест экспорта данных бронирования в JSON."""
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            filepath = temp_file.name
        
        try:
            # Экспортируем данные
            result = await JsonExporter.export_booking_data(filepath, self.booking_data)
            
            # Проверяем, что файл создан
            self.assertTrue(os.path.exists(filepath))
            self.assertEqual(result, filepath)
            
            # Проверяем содержимое файла
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Проверяем структуру данных
                self.assertIsInstance(data, list)
                self.assertEqual(len(data), 2)
                
                # Проверяем содержимое
                self.assertEqual(data[0]["id"], 1)
                self.assertEqual(data[0]["url"], "https://example.com")
                self.assertEqual(data[0]["date"], "2023-01-01")
                self.assertEqual(data[0]["time"], "12:00:00")
                self.assertEqual(data[0]["price"], "1000")
                self.assertEqual(data[0]["provider"], "Provider 1")
                self.assertEqual(data[0]["seat_number"], "1")
                
                self.assertEqual(data[1]["id"], 2)
                self.assertEqual(data[1]["additional_field"], "Additional value")
        
        finally:
            # Удаляем временный файл
            if os.path.exists(filepath):
                os.remove(filepath)
    
    @pytest.mark.asyncio
    async def test_export_urls(self):
        """Тест экспорта URL в JSON."""
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            filepath = temp_file.name
        
        try:
            # Экспортируем данные
            result = await JsonExporter.export_urls(filepath, self.urls)
            
            # Проверяем, что файл создан
            self.assertTrue(os.path.exists(filepath))
            self.assertEqual(result, filepath)
            
            # Проверяем содержимое файла
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Проверяем структуру данных
                self.assertIsInstance(data, list)
                self.assertEqual(len(data), 2)
                
                # Проверяем содержимое
                self.assertEqual(data[0]["id"], 1)
                self.assertEqual(data[0]["url"], "https://example1.com")
                self.assertEqual(data[0]["title"], "Example 1")
                self.assertEqual(data[0]["description"], "Example description 1")
                self.assertEqual(data[0]["is_active"], True)
                
                self.assertEqual(data[1]["id"], 2)
                self.assertEqual(data[1]["url"], "https://example2.com")
                self.assertEqual(data[1]["title"], "Example 2")
                self.assertEqual(data[1]["description"], "Example description 2")
                self.assertEqual(data[1]["is_active"], False)
        
        finally:
            # Удаляем временный файл
            if os.path.exists(filepath):
                os.remove(filepath)
    
    @pytest.mark.asyncio
    async def test_export_statistics(self):
        """Тест экспорта статистики в JSON."""
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            filepath = temp_file.name
        
        try:
            # Экспортируем данные
            result = await JsonExporter.export_statistics(filepath, self.statistics)
            
            # Проверяем, что файл создан
            self.assertTrue(os.path.exists(filepath))
            self.assertEqual(result, filepath)
            
            # Проверяем содержимое файла
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Проверяем структуру данных
                self.assertIsInstance(data, dict)
                
                # Проверяем содержимое
                self.assertEqual(data["url_count"], 2)
                self.assertEqual(data["booking_count"], 10)
                self.assertEqual(len(data["date_stats"]), 2)
                self.assertEqual(len(data["url_stats"]), 2)
                self.assertEqual(data["date_stats"][0]["date"], "2023-01-01")
                self.assertEqual(data["date_stats"][0]["count"], 5)
                self.assertEqual(data["url_stats"][0]["url"], "https://example1.com")
                self.assertEqual(data["url_stats"][0]["count"], 5)
        
        finally:
            # Удаляем временный файл
            if os.path.exists(filepath):
                os.remove(filepath)


if __name__ == '__main__':
    unittest.main()
