"""
Test API - Модульные тесты для API парсера YCLIENTS.

Модуль содержит тесты для API-компонентов приложения.
"""
import json
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes import app
from src.api.auth import get_api_key
from config.settings import API_KEY


# Мокируем зависимость API-ключа для тестирования
async def override_get_api_key():
    return API_KEY


app.dependency_overrides[get_api_key] = override_get_api_key


class TestAPI(unittest.TestCase):
    """Тесты для API-компонентов."""
    
    def setUp(self):
        """Настройка тестов."""
        self.client = TestClient(app)
        
        # Тестовые данные
        self.test_url = {
            "id": 1,
            "url": "https://example.com",
            "title": "Example",
            "description": "Example description",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "is_active": True
        }
        
        self.test_booking_data = {
            "id": 1,
            "url": "https://example.com",
            "date": "2023-01-01",
            "time": "12:00:00",
            "price": "1000",
            "provider": "Provider",
            "seat_number": "1",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def test_read_root(self):
        """Тест корневого эндпоинта."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "YCLIENTS Parser API работает")
        self.assertIn("data", data)
        self.assertIn("version", data["data"])
    
    @patch('src.api.routes.db_manager')
    def test_get_status(self, mock_db_manager):
        """Тест эндпоинта получения статуса."""
        # Мокаем метод get_statistics
        mock_db_manager.get_statistics = AsyncMock(return_value={
            "url_count": 1,
            "booking_count": 1,
            "date_stats": [],
            "url_stats": []
        })
        
        # Вызываем API-эндпоинт
        response = self.client.get("/status", headers={"X-API-Key": API_KEY})
        
        # Проверяем ответ
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "Статус парсера получен")
        self.assertIn("data", data)
        self.assertIn("url_count", data["data"])
        self.assertIn("booking_count", data["data"])
    
    @patch('src.api.routes.db_manager')
    def test_get_urls(self, mock_db_manager):
        """Тест эндпоинта получения списка URL."""
        # Мокаем метод get_all
        mock_db_manager.pool = MagicMock()
        mock_db_manager.url_table = "urls"
        
        # Мокаем асинхронные методы
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[{
            "id": 1,
            "url": "https://example.com",
            "title": "Example",
            "description": "Example description",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "is_active": True
        }])
        
        mock_db_manager.pool.acquire = AsyncMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock()
        ))
        
        # Вызываем API-эндпоинт
        response = self.client.get("/urls", headers={"X-API-Key": API_KEY})
        
        # Проверяем ответ
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("Получено", data["message"])
        self.assertIn("data", data)
        self.assertIsInstance(data["data"], list)
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0]["url"], "https://example.com")
    
    @patch('src.api.routes.db_manager')
    def test_create_url(self, mock_db_manager):
        """Тест эндпоинта создания URL."""
        # Мокаем метод get_or_create_url
        mock_db_manager.pool = MagicMock()
        mock_db_manager.url_table = "urls"
        
        # Мокаем асинхронные методы
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(side_effect=[None, 1])
        mock_conn.fetchrow = AsyncMock(return_value=self.test_url)
        
        mock_db_manager.pool.acquire = AsyncMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock()
        ))
        
        # Подготавливаем данные для запроса
        url_data = {
            "url": "https://example.com",
            "title": "Example",
            "description": "Example description"
        }
        
        # Вызываем API-эндпоинт
        response = self.client.post(
            "/urls",
            json=url_data,
            headers={"X-API-Key": API_KEY}
        )
        
        # Проверяем ответ
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "URL успешно создан")
        self.assertIn("data", data)
        self.assertEqual(data["data"]["url"], "https://example.com")
    
    @patch('src.api.routes.db_manager')
    def test_get_booking_data(self, mock_db_manager):
        """Тест эндпоинта получения данных бронирования."""
        # Мокаем метод get_booking_data
        mock_db_manager.pool = MagicMock()
        mock_db_manager.booking_table = "booking_data"
        mock_db_manager.url_table = "urls"
        
        # Мокаем асинхронные методы
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=10)
        mock_conn.fetch = AsyncMock(return_value=[{
            "id": 1,
            "url": "https://example.com",
            "date": datetime.now().date(),
            "time": datetime.now().time(),
            "price": "1000",
            "provider": "Provider",
            "seat_number": "1",
            "extra_data": json.dumps({"key": "value"}),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }])
        
        mock_db_manager.pool.acquire = AsyncMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock()
        ))
        
        # Вызываем API-эндпоинт
        response = self.client.get("/data", headers={"X-API-Key": API_KEY})
        
        # Проверяем ответ
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("Получено", data["message"])
        self.assertIn("data", data)
        self.assertIn("items", data["data"])
        self.assertIsInstance(data["data"]["items"], list)
        self.assertEqual(len(data["data"]["items"]), 1)
        self.assertEqual(data["data"]["items"][0]["price"], "1000")
    
    @patch('src.api.routes.db_manager')
    @patch('src.api.routes.BackgroundTasks')
    def test_export_data(self, mock_background_tasks, mock_db_manager):
        """Тест эндпоинта экспорта данных."""
        # Мокаем метод export_to_csv/export_to_json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filepath = f"data/export/booking_data_{timestamp}.csv"
        
        mock_db_manager.export_to_csv = AsyncMock(return_value=csv_filepath)
        mock_db_manager.export_to_json = AsyncMock(return_value=csv_filepath.replace(".csv", ".json"))
        mock_db_manager.export_path = "data/export"
        
        # Вызываем API-эндпоинт для CSV
        response = self.client.get(
            "/export?format=csv",
            headers={"X-API-Key": API_KEY}
        )
        
        # Проверяем ответ
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("данные успешно экспортированы", data["message"].lower())
        self.assertIn("data", data)
        self.assertIn("filename", data["data"])
        self.assertIn("url", data["data"])
        
        # Вызываем API-эндпоинт для JSON
        response = self.client.get(
            "/export?format=json",
            headers={"X-API-Key": API_KEY}
        )
        
        # Проверяем ответ
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("данные успешно экспортированы", data["message"].lower())
    
    @patch('src.api.routes.run_parser_task')
    @patch('src.api.routes.BackgroundTasks')
    def test_run_parser(self, mock_background_tasks, mock_run_parser_task):
        """Тест эндпоинта запуска парсера."""
        # Мокаем методы
        mock_background_tasks.add_task = MagicMock()
        
        # Вызываем API-эндпоинт
        response = self.client.post(
            "/parse?url=https://example.com",
            headers={"X-API-Key": API_KEY}
        )
        
        # Проверяем ответ
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("Парсер запущен", data["message"])
    
    def test_invalid_api_key(self):
        """Тест с недействительным API-ключом."""
        # Временно отключаем переопределение зависимости
        app.dependency_overrides = {}
        
        # Вызываем API-эндпоинт с недействительным ключом
        response = self.client.get("/status", headers={"X-API-Key": "invalid_key"})
        
        # Проверяем ответ
        self.assertEqual(response.status_code, 403)
        
        data = response.json()
        self.assertEqual(data["detail"], "Недействительный API-ключ")
        
        # Вызываем API-эндпоинт без ключа
        response = self.client.get("/status")
        
        # Проверяем ответ
        self.assertEqual(response.status_code, 401)
        
        data = response.json()
        self.assertEqual(data["detail"], "API-ключ не предоставлен")
        
        # Восстанавливаем переопределение зависимости
        app.dependency_overrides[get_api_key] = override_get_api_key


if __name__ == '__main__':
    unittest.main()
