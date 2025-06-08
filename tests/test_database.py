"""
Test Database - Модульные тесты для работы с базой данных.

Модуль содержит тесты для компонентов работы с базой данных.
"""
import asyncio
import json
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
import asyncpg

from src.database.db_manager import DatabaseManager
from src.database.models import Url, BookingData
from src.database.queries import UrlQueries, BookingQueries


class TestDatabaseModels(unittest.TestCase):
    """Тесты для моделей данных."""
    
    def test_url_model(self):
        """Тест модели URL."""
        # Создаем объект URL
        url = Url(
            id=1,
            url="https://example.com",
            title="Example",
            description="Example description",
            created_at=datetime(2023, 1, 1, 0, 0, 0),
            updated_at=datetime(2023, 1, 1, 0, 0, 0),
            is_active=True
        )
        
        # Проверяем свойства объекта
        self.assertEqual(url.id, 1)
        self.assertEqual(url.url, "https://example.com")
        self.assertEqual(url.title, "Example")
        self.assertEqual(url.description, "Example description")
        self.assertEqual(url.created_at, datetime(2023, 1, 1, 0, 0, 0))
        self.assertEqual(url.updated_at, datetime(2023, 1, 1, 0, 0, 0))
        self.assertEqual(url.is_active, True)
        
        # Тест to_dict
        url_dict = url.to_dict()
        self.assertEqual(url_dict["id"], 1)
        self.assertEqual(url_dict["url"], "https://example.com")
        self.assertEqual(url_dict["title"], "Example")
        self.assertEqual(url_dict["description"], "Example description")
        self.assertEqual(url_dict["created_at"], "2023-01-01T00:00:00")
        self.assertEqual(url_dict["updated_at"], "2023-01-01T00:00:00")
        self.assertEqual(url_dict["is_active"], True)
        
        # Тест from_dict
        url2 = Url.from_dict(url_dict)
        self.assertEqual(url2.id, 1)
        self.assertEqual(url2.url, "https://example.com")
        self.assertEqual(url2.title, "Example")
        self.assertEqual(url2.description, "Example description")
        self.assertEqual(url2.created_at, datetime(2023, 1, 1, 0, 0, 0))
        self.assertEqual(url2.updated_at, datetime(2023, 1, 1, 0, 0, 0))
        self.assertEqual(url2.is_active, True)
    
    def test_booking_data_model(self):
        """Тест модели данных бронирования."""
        # Создаем объект BookingData
        booking_data = BookingData(
            id=1,
            url_id=1,
            url="https://example.com",
            date="2023-01-01",
            time="12:00:00",
            price="1000",
            provider="Provider",
            seat_number="1",
            extra_data={"key": "value"},
            created_at=datetime(2023, 1, 1, 0, 0, 0),
            updated_at=datetime(2023, 1, 1, 0, 0, 0)
        )
        
        # Проверяем свойства объекта
        self.assertEqual(booking_data.id, 1)
        self.assertEqual(booking_data.url_id, 1)
        self.assertEqual(booking_data.url, "https://example.com")
        self.assertEqual(booking_data.date, "2023-01-01")
        self.assertEqual(booking_data.time, "12:00:00")
        self.assertEqual(booking_data.price, "1000")
        self.assertEqual(booking_data.provider, "Provider")
        self.assertEqual(booking_data.seat_number, "1")
        self.assertEqual(booking_data.extra_data, {"key": "value"})
        self.assertEqual(booking_data.created_at, datetime(2023, 1, 1, 0, 0, 0))
        self.assertEqual(booking_data.updated_at, datetime(2023, 1, 1, 0, 0, 0))
        
        # Тест to_dict
        booking_dict = booking_data.to_dict()
        self.assertEqual(booking_dict["id"], 1)
        self.assertEqual(booking_dict["url_id"], 1)
        self.assertEqual(booking_dict["url"], "https://example.com")
        self.assertEqual(booking_dict["date"], "2023-01-01")
        self.assertEqual(booking_dict["time"], "12:00:00")
        self.assertEqual(booking_dict["price"], "1000")
        self.assertEqual(booking_dict["provider"], "Provider")
        self.assertEqual(booking_dict["seat_number"], "1")
        self.assertEqual(booking_dict["created_at"], "2023-01-01T00:00:00")
        self.assertEqual(booking_dict["updated_at"], "2023-01-01T00:00:00")
        self.assertEqual(booking_dict["key"], "value")
        
        # Тест from_dict
        booking_data2 = BookingData.from_dict(booking_dict)
        self.assertEqual(booking_data2.id, 1)
        self.assertEqual(booking_data2.url_id, 1)
        self.assertEqual(booking_data2.url, "https://example.com")
        self.assertEqual(booking_data2.date, "2023-01-01")
        self.assertEqual(booking_data2.time, "12:00:00")
        self.assertEqual(booking_data2.price, "1000")
        self.assertEqual(booking_data2.provider, "Provider")
        self.assertEqual(booking_data2.seat_number, "1")
        self.assertEqual(booking_data2.extra_data, {"key": "value"})
        self.assertEqual(booking_data2.created_at, datetime(2023, 1, 1, 0, 0, 0))
        self.assertEqual(booking_data2.updated_at, datetime(2023, 1, 1, 0, 0, 0))


class TestDatabaseQueries(unittest.TestCase):
    """Тесты для запросов к базе данных."""
    
    def test_url_queries(self):
        """Тест запросов для таблицы URL."""
        # Тест запроса всех URL
        query, params = UrlQueries.get_all()
        self.assertIn("SELECT * FROM", query)
        self.assertIn("ORDER BY id", query)
        self.assertEqual(params, [])
        
        # Тест запроса всех активных URL
        query, params = UrlQueries.get_all(active_only=True)
        self.assertIn("WHERE is_active = $1", query)
        self.assertEqual(params, [True])
        
        # Тест запроса URL по ID
        query, params = UrlQueries.get_by_id(1)
        self.assertIn("WHERE id = $1", query)
        self.assertEqual(params, [1])
        
        # Тест запроса URL по URL
        query, params = UrlQueries.get_by_url("https://example.com")
        self.assertIn("WHERE url = $1", query)
        self.assertEqual(params, ["https://example.com"])
        
        # Тест создания URL
        query, params = UrlQueries.create(
            "https://example.com",
            "Example",
            "Example description"
        )
        self.assertIn("INSERT INTO", query)
        self.assertIn("VALUES ($1, $2, $3, TRUE)", query)
        self.assertEqual(params, ["https://example.com", "Example", "Example description"])
        
        # Тест обновления URL
        query, params = UrlQueries.update(1, "New title", "New description", False)
        self.assertIn("UPDATE", query)
        self.assertIn("SET title = $1, description = $2, is_active = $3", query)
        self.assertIn("WHERE id = $4", query)
        self.assertEqual(params, ["New title", "New description", False, 1])
        
        # Тест удаления URL
        query, params = UrlQueries.delete(1)
        self.assertIn("DELETE FROM", query)
        self.assertIn("WHERE id = $1", query)
        self.assertEqual(params, [1])
    
    def test_booking_queries(self):
        """Тест запросов для таблицы данных бронирования."""
        # Тест запроса всех данных бронирования
        query, params = BookingQueries.get_all()
        self.assertIn("SELECT b.id, u.url, b.date, b.time", query)
        self.assertIn("FROM booking_data b", query)
        self.assertIn("JOIN urls u ON b.url_id = u.id", query)
        self.assertIn("WHERE 1=1", query)
        self.assertIn("ORDER BY b.date DESC, b.time DESC", query)
        self.assertIn("LIMIT $1 OFFSET $2", query)
        self.assertEqual(params, [100, 0])
        
        # Тест запроса данных бронирования с фильтрами
        query, params = BookingQueries.get_all(
            url_id=1,
            url="https://example.com",
            date_from="2023-01-01",
            date_to="2023-01-31",
            limit=10,
            offset=5
        )
        self.assertIn("WHERE 1=1", query)
        self.assertIn("AND u.id = $1", query)
        self.assertIn("AND u.url = $2", query)
        self.assertIn("AND b.date >= $3", query)
        self.assertIn("AND b.date <= $4", query)
        self.assertIn("ORDER BY b.date DESC, b.time DESC LIMIT $5 OFFSET $6", query)
        self.assertEqual(params, [1, "https://example.com", "2023-01-01", "2023-01-31", 10, 5])
        
        # Тест запроса количества данных бронирования
        query, params = BookingQueries.count()
        self.assertIn("SELECT COUNT(*)", query)
        self.assertIn("FROM booking_data b", query)
        self.assertIn("JOIN urls u ON b.url_id = u.id", query)
        self.assertIn("WHERE 1=1", query)
        self.assertEqual(params, [])
        
        # Тест создания данных бронирования
        query, params = BookingQueries.create(
            url_id=1,
            date="2023-01-01",
            time="12:00:00",
            price="1000",
            provider="Provider",
            seat_number="1",
            extra_data={"key": "value"}
        )
        self.assertIn("INSERT INTO booking_data", query)
        self.assertIn("ON CONFLICT (url_id, date, time, seat_number) DO UPDATE", query)
        self.assertEqual(params, [1, "2023-01-01", "12:00:00", "1000", "Provider", "1", {"key": "value"}])
        
        # Тест удаления данных бронирования
        query, params = BookingQueries.delete(1)
        self.assertIn("DELETE FROM booking_data", query)
        self.assertIn("WHERE id = $1", query)
        self.assertEqual(params, [1])
        
        # Тест удаления данных бронирования по ID URL
        query, params = BookingQueries.delete_by_url_id(1)
        self.assertIn("DELETE FROM booking_data", query)
        self.assertIn("WHERE url_id = $1", query)
        self.assertEqual(params, [1])
        
        # Тест удаления устаревших данных
        query, params = BookingQueries.delete_old_data(30)
        self.assertIn("DELETE FROM booking_data", query)
        self.assertIn("WHERE date < CURRENT_DATE - $1::interval", query)
        self.assertEqual(params, ["30 days"])


class TestDatabaseManager(unittest.TestCase):
    """Тесты для менеджера базы данных."""
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Тест инициализации соединения с базой данных."""
        # Создаем моки
        mock_supabase = MagicMock()
        mock_pool = MagicMock()
        
        # Мокаем асинхронные методы
        mock_supabase.auth.get_user = AsyncMock()
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value="PostgreSQL 14.0")
        mock_pool.acquire = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock()))
        
        # Создаем экземпляр DatabaseManager
        with patch('src.database.db_manager.create_client', return_value=mock_supabase), \
             patch('asyncpg.create_pool', AsyncMock(return_value=mock_pool)):
            db_manager = DatabaseManager()
            
            # Вызываем тестируемый метод
            await db_manager.initialize()
            
            # Проверяем, что методы были вызваны
            mock_supabase.auth.get_user.assert_called_once()
            mock_conn.fetchval.assert_called_once()
            
            # Проверяем, что атрибуты установлены
            self.assertEqual(db_manager.supabase, mock_supabase)
            self.assertEqual(db_manager.pool, mock_pool)
            self.assertTrue(db_manager.is_initialized)
    
    @pytest.mark.asyncio
    async def test_close(self):
        """Тест закрытия соединения с базой данных."""
        # Создаем моки
        mock_pool = MagicMock()
        
        # Мокаем асинхронные методы
        mock_pool.close = AsyncMock()
        
        # Создаем экземпляр DatabaseManager
        db_manager = DatabaseManager()
        db_manager.pool = mock_pool
        
        # Вызываем тестируемый метод
        await db_manager.close()
        
        # Проверяем, что методы были вызваны
        mock_pool.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_or_create_url(self):
        """Тест получения или создания URL."""
        # Создаем моки
        mock_conn = MagicMock()
        mock_pool = MagicMock()
        
        # Мокаем асинхронные методы
        mock_conn.fetchval = AsyncMock(side_effect=[None, 1])
        mock_conn.execute = AsyncMock()
        mock_pool.acquire = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock()))
        
        # Создаем экземпляр DatabaseManager
        db_manager = DatabaseManager()
        db_manager.pool = mock_pool
        
        # Вызываем тестируемый метод
        url_id = await db_manager.get_or_create_url("https://example.com", "Example", "Example description")
        
        # Проверяем, что методы были вызваны
        mock_conn.fetchval.assert_any_call("SELECT id FROM urls WHERE url = $1", "https://example.com")
        mock_conn.fetchval.assert_any_call(
            "INSERT INTO urls (url, title, description) VALUES ($1, $2, $3) RETURNING id",
            "https://example.com", "Example", "Example description"
        )
        mock_conn.execute.assert_called_once()
        
        # Проверяем, что возвращаемое значение корректно
        self.assertEqual(url_id, 1)


if __name__ == '__main__':
    unittest.main()
