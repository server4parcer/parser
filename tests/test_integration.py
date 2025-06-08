"""
Test Integration - Интеграционные тесты для парсера YCLIENTS.

Модуль содержит интеграционные тесты для проверки всей системы в целом.
"""
import asyncio
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from playwright.async_api import BrowserContext, Browser, Page

from src.browser.browser_manager import BrowserManager
from src.browser.proxy_manager import ProxyManager
from src.database.db_manager import DatabaseManager
from src.parser.data_extractor import DataExtractor
from src.parser.yclients_parser import YClientsParser
from src.export.csv_exporter import CsvExporter
from src.export.json_exporter import JsonExporter


class TestIntegration(unittest.TestCase):
    """Интеграционные тесты для проверки взаимодействия компонентов."""
    
    @pytest.mark.asyncio
    async def test_full_parser_flow(self):
        """Тест полного процесса парсинга."""
        # Мокаем playwright, чтобы избежать реальных запросов
        mock_page = MagicMock(spec=Page)
        mock_context = MagicMock(spec=BrowserContext)
        mock_browser = MagicMock(spec=Browser)
        
        # Мокаем асинхронные методы
        mock_browser.close = AsyncMock()
        mock_context.close = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        
        # Мокаем селекторы и методы страницы
        date_elements = [
            MagicMock(text_content=AsyncMock(return_value="1 января")),
            MagicMock(text_content=AsyncMock(return_value="2 января"))
        ]
        for i, element in enumerate(date_elements):
            element.get_attribute = AsyncMock(return_value=f"2023-01-0{i+1}")
        
        slot_elements = [
            MagicMock(text_content=AsyncMock(return_value="10:00")),
            MagicMock(text_content=AsyncMock(return_value="12:00"))
        ]
        
        price_element = MagicMock(text_content=AsyncMock(return_value="1000 руб"))
        provider_element = MagicMock(text_content=AsyncMock(return_value="Тренер Иванов"))
        seat_element = MagicMock(text_content=AsyncMock(return_value="Корт 1"))
        
        mock_page.query_selector_all = AsyncMock(side_effect=[
            date_elements,  # Для available_dates
            slot_elements,  # Для time_slots
        ])
        
        mock_page.query_selector = AsyncMock(side_effect=[
            MagicMock(click=AsyncMock()),  # Для date_selector
            None,  # Для captcha
            None,  # Для ip_blocked
            MagicMock(),  # Для calendar
            MagicMock()   # Для time_slots_container
        ])
        
        mock_slot = MagicMock()
        mock_slot.query_selector = AsyncMock(side_effect=[
            price_element,
            provider_element,
            seat_element
        ])
        slot_elements[0].query_selector = mock_slot.query_selector
        slot_elements[1].query_selector = mock_slot.query_selector
        
        mock_page.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_page.wait_for_selector = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        
        # Мокаем базу данных и её методы
        mock_db_manager = MagicMock(spec=DatabaseManager)
        mock_db_manager.get_or_create_url = AsyncMock(return_value=1)
        mock_db_manager.save_booking_data = AsyncMock(return_value=(2, 0))
        
        # Создаем парсер с мокированными зависимостями
        with patch('src.parser.yclients_parser.BrowserManager', return_value=MagicMock(spec=BrowserManager)), \
             patch('src.parser.yclients_parser.ProxyManager', return_value=MagicMock(spec=ProxyManager)), \
             patch('src.parser.yclients_parser.DataExtractor', return_value=MagicMock(spec=DataExtractor)):
            parser = YClientsParser(["https://yclients.com/company/111111/booking"], mock_db_manager)
            
            # Устанавливаем мокированный браузер
            parser.browser = mock_browser
            parser.context = mock_context
            parser.page = mock_page
            
            # Мокируем extract_booking_data_from_slot, чтобы возвращать предопределенные данные
            parser.data_extractor.extract_booking_data_from_slot = AsyncMock(side_effect=[
                {
                    "time": "10:00:00",
                    "price": "1000 руб",
                    "provider": "Тренер Иванов",
                    "seat_number": "1"
                },
                {
                    "time": "12:00:00",
                    "price": "1500 руб",
                    "provider": "Тренер Петров",
                    "seat_number": "2"
                }
            ])
            
            # Запускаем парсинг
            success, data = await parser.parse_url("https://yclients.com/company/111111/booking")
            
            # Проверяем результаты
            self.assertTrue(success)
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 2)
            
            # Проверяем вызовы методов
            mock_page.goto.assert_called_once()
            mock_page.query_selector_all.assert_called()
            parser.data_extractor.extract_booking_data_from_slot.assert_called()
            
            # Проверяем сохранение данных
            mock_db_manager.save_booking_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_database_and_export_integration(self):
        """Тест интеграции базы данных и экспорта."""
        # Создаем тестовые данные
        booking_data = [
            {
                "id": 1,
                "url_id": 1,
                "url": "https://example.com",
                "date": "2023-01-01",
                "time": "10:00:00",
                "price": "1000 руб",
                "provider": "Тренер Иванов",
                "seat_number": "1",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": 2,
                "url_id": 1,
                "url": "https://example.com",
                "date": "2023-01-01",
                "time": "12:00:00",
                "price": "1500 руб",
                "provider": "Тренер Петров",
                "seat_number": "2",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
        
        # Мокаем базу данных
        mock_db_manager = MagicMock(spec=DatabaseManager)
        mock_db_manager.get_booking_data = AsyncMock(return_value=booking_data)
        
        # Создаем временные файлы для экспорта
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as csv_file, \
             tempfile.NamedTemporaryFile(suffix='.json', delete=False) as json_file:
            csv_filepath = csv_file.name
            json_filepath = json_file.name
        
        try:
            # Экспортируем данные
            with patch('src.export.csv_exporter.CsvExporter.export_booking_data', AsyncMock(return_value=csv_filepath)), \
                 patch('src.export.json_exporter.JsonExporter.export_booking_data', AsyncMock(return_value=json_filepath)):
                
                # Экспортируем в CSV и JSON
                csv_result = await mock_db_manager.export_to_csv(csv_filepath)
                json_result = await mock_db_manager.export_to_json(json_filepath)
                
                # Проверяем результаты
                self.assertEqual(csv_result, csv_filepath)
                self.assertEqual(json_result, json_filepath)
                
                # Проверяем вызовы методов
                mock_db_manager.get_booking_data.assert_called()
                CsvExporter.export_booking_data.assert_called_once()
                JsonExporter.export_booking_data.assert_called_once()
        
        finally:
            # Удаляем временные файлы
            for filepath in [csv_filepath, json_filepath]:
                if os.path.exists(filepath):
                    os.remove(filepath)
    
    @pytest.mark.asyncio
    async def test_scheduler_integration(self):
        """Тест интеграции планировщика парсинга."""
        # Мокаем парсер
        mock_parser = MagicMock(spec=YClientsParser)
        mock_parser.run_single_iteration = AsyncMock()
        
        # Мокаем время для ускорения теста
        with patch('time.time', side_effect=[0, 10, 20]), \
             patch('asyncio.sleep', AsyncMock()), \
             patch('src.scheduler.cron_manager.cron_manager') as mock_cron_manager:
            
            # Настраиваем менеджер cron
            mock_cron_manager.start = AsyncMock()
            mock_cron_manager.add_task = AsyncMock()
            
            # Импортируем здесь, чтобы мок успел применитьс я
            from src.scheduler.cron_manager import setup_cron
            
            # Запускаем настройку cron
            urls = ["https://example.com"]
            await setup_cron(mock_parser.run_single_iteration, urls)
            
            # Проверяем вызовы методов
            mock_cron_manager.start.assert_called_once()
            mock_cron_manager.add_task.assert_called_once()
            
            # Проверяем параметры вызова add_task
            args, kwargs = mock_cron_manager.add_task.call_args
            self.assertEqual(args[0], "parsing")
            self.assertEqual(args[1], mock_parser.run_single_iteration)
            self.assertIsInstance(args[2], int)  # Интервал парсинга
            self.assertEqual(args[3], urls)


class TestEnd2End(unittest.TestCase):
    """
    Симуляция полного цикла работы приложения.
    
    Эти тесты используют моки для избежания реальных внешних зависимостей,
    но симулируют полный поток данных через систему.
    """
    
    @pytest.mark.asyncio
    async def test_full_application_flow(self):
        """Тест полного цикла работы приложения."""
        # Тестовые URL для парсинга
        test_urls = ["https://yclients.com/company/111111/booking"]
        
        # Тестовые данные бронирования
        test_booking_data = [
            {
                "date": "2023-01-01",
                "time": "10:00:00",
                "price": "1000 руб",
                "provider": "Тренер Иванов",
                "seat_number": "1"
            },
            {
                "date": "2023-01-01",
                "time": "12:00:00",
                "price": "1500 руб",
                "provider": "Тренер Петров",
                "seat_number": "2"
            }
        ]
        
        # Мокаем все компоненты системы
        
        # 1. БД менеджер
        mock_db_manager = MagicMock(spec=DatabaseManager)
        mock_db_manager.initialize = AsyncMock()
        mock_db_manager.get_or_create_url = AsyncMock(return_value=1)
        mock_db_manager.save_booking_data = AsyncMock(return_value=(2, 0))
        mock_db_manager.export_to_csv = AsyncMock(return_value="data/export/booking_data.csv")
        mock_db_manager.export_to_json = AsyncMock(return_value="data/export/booking_data.json")
        mock_db_manager.close = AsyncMock()
        
        # 2. Парсер
        mock_parser = MagicMock(spec=YClientsParser)
        mock_parser.run_single_iteration = AsyncMock()
        mock_parser.initialize = AsyncMock()
        mock_parser.parse_url = AsyncMock(return_value=(True, test_booking_data))
        mock_parser.parse_all_urls = AsyncMock(return_value={test_urls[0]: test_booking_data})
        mock_parser.close = AsyncMock()
        
        # 3. Браузер менеджер
        mock_browser_manager = MagicMock(spec=BrowserManager)
        mock_browser_manager.initialize_browser = AsyncMock(return_value=(MagicMock(), MagicMock()))
        
        # 4. Прокси менеджер
        mock_proxy_manager = MagicMock(spec=ProxyManager)
        mock_proxy_manager.get_next_proxy = MagicMock(return_value={})
        
        # 5. Экстрактор данных
        mock_data_extractor = MagicMock(spec=DataExtractor)
        mock_data_extractor.extract_booking_data_from_slot = AsyncMock(side_effect=test_booking_data)
        
        # Инициализация системы
        with patch('src.parser.yclients_parser.DatabaseManager', return_value=mock_db_manager), \
             patch('src.parser.yclients_parser.BrowserManager', return_value=mock_browser_manager), \
             patch('src.parser.yclients_parser.ProxyManager', return_value=mock_proxy_manager), \
             patch('src.parser.yclients_parser.DataExtractor', return_value=mock_data_extractor):
            
            # Создаем экземпляр парсера
            parser = YClientsParser(test_urls, mock_db_manager)
            
            # Запускаем одну итерацию парсинга
            await parser.run_single_iteration()
            
            # Проверяем, что методы были вызваны в правильном порядке
            mock_db_manager.initialize.assert_called_once()
            parser.parse_all_urls.assert_called_once()
            mock_db_manager.save_booking_data.assert_called()
            
            # Экспортируем данные
            csv_filepath = await mock_db_manager.export_to_csv()
            json_filepath = await mock_db_manager.export_to_json()
            
            # Проверяем результаты экспорта
            self.assertEqual(csv_filepath, "data/export/booking_data.csv")
            self.assertEqual(json_filepath, "data/export/booking_data.json")
            
            # Закрываем подключение к БД
            await mock_db_manager.close()
            mock_db_manager.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
