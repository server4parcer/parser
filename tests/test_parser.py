"""
Test Parser - Модульные тесты для парсера YCLIENTS.

Модуль содержит тесты для компонентов парсера.
"""
import asyncio
import os
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from playwright.async_api import Page, BrowserContext, Browser

from src.parser.yclients_parser import YClientsParser
from src.browser.browser_manager import BrowserManager
from src.browser.proxy_manager import ProxyManager
from src.parser.data_extractor import DataExtractor


class TestBrowserManager(unittest.TestCase):
    """Тесты для менеджера браузера."""
    
    @pytest.mark.asyncio
    async def test_initialize_browser(self):
        """Тест инициализации браузера."""
        # Создаем моки
        mock_browser = MagicMock(spec=Browser)
        mock_context = MagicMock(spec=BrowserContext)
        
        # Мокаем асинхронные методы
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        
        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.stop = AsyncMock()
        
        # Создаем экземпляр BrowserManager
        browser_manager = BrowserManager()
        
        # Перезаписываем атрибут playwright
        browser_manager.playwright = mock_playwright
        
        # Вызываем тестируемый метод
        browser, context = await browser_manager.initialize_browser()
        
        # Проверяем, что методы были вызваны
        mock_playwright.chromium.launch.assert_called_once()
        mock_browser.new_context.assert_called_once()
        
        # Проверяем, что возвращаемые значения корректны
        self.assertEqual(browser, mock_browser)
        self.assertEqual(context, mock_context)
    
    def test_get_random_user_agent(self):
        """Тест получения случайного User-Agent."""
        browser_manager = BrowserManager()
        user_agent = browser_manager.get_random_user_agent()
        
        # Проверяем, что User-Agent не пустой
        self.assertIsNotNone(user_agent)
        self.assertGreater(len(user_agent), 0)
        
        # Проверяем, что User-Agent из списка
        self.assertIn(user_agent, browser_manager.user_agents)
    
    def test_get_random_viewport(self):
        """Тест получения случайного размера окна."""
        browser_manager = BrowserManager()
        viewport = browser_manager.get_random_viewport()
        
        # Проверяем, что размер окна не пустой
        self.assertIsNotNone(viewport)
        
        # Проверяем, что размер окна содержит необходимые ключи
        self.assertIn('width', viewport)
        self.assertIn('height', viewport)
        
        # Проверяем, что размер окна из списка
        self.assertIn(viewport, browser_manager.viewport_sizes)
    
    def test_get_random_delay(self):
        """Тест получения случайной задержки."""
        browser_manager = BrowserManager()
        
        # Проверяем с дефолтными параметрами
        delay = browser_manager.get_random_delay()
        self.assertGreaterEqual(delay, 0.5)
        self.assertLessEqual(delay, 2.0)
        
        # Проверяем с заданными параметрами
        min_delay = 1.0
        max_delay = 3.0
        delay = browser_manager.get_random_delay(min_delay, max_delay)
        self.assertGreaterEqual(delay, min_delay)
        self.assertLessEqual(delay, max_delay)


class TestProxyManager(unittest.TestCase):
    """Тесты для менеджера прокси."""
    
    def setUp(self):
        """Настройка тестов."""
        # Создаем тестовый список прокси
        self.test_proxies = [
            {
                "server": "proxy1.example.com",
                "username": "user1",
                "password": "pass1",
                "port": 8080
            },
            {
                "server": "proxy2.example.com",
                "username": "user2",
                "password": "pass2",
                "port": 8080
            }
        ]
    
    def test_load_proxies_from_env(self):
        """Тест загрузки прокси из переменных окружения."""
        # Устанавливаем переменные окружения
        os.environ['PROXY_SERVERS'] = 'proxy1.example.com,proxy2.example.com'
        os.environ['PROXY_USERNAMES'] = 'user1,user2'
        os.environ['PROXY_PASSWORDS'] = 'pass1,pass2'
        os.environ['PROXY_PORTS'] = '8080,8080'
        
        # Создаем экземпляр ProxyManager с мокированной загрузкой из файла
        with patch('os.path.exists', return_value=False):
            proxy_manager = ProxyManager()
        
        # Проверяем, что прокси загружены из переменных окружения
        self.assertEqual(len(proxy_manager.proxies), 2)
        
        # Проверяем, что прокси содержат правильные данные
        self.assertEqual(proxy_manager.proxies[0]['server'], 'proxy1.example.com')
        self.assertEqual(proxy_manager.proxies[0]['username'], 'user1')
        self.assertEqual(proxy_manager.proxies[0]['password'], 'pass1')
        self.assertEqual(proxy_manager.proxies[0]['port'], 8080)
        
        # Восстанавливаем переменные окружения
        del os.environ['PROXY_SERVERS']
        del os.environ['PROXY_USERNAMES']
        del os.environ['PROXY_PASSWORDS']
        del os.environ['PROXY_PORTS']
    
    def test_format_proxy_url(self):
        """Тест форматирования URL прокси."""
        proxy_manager = ProxyManager()
        
        # Тест с полным набором данных
        proxy = {
            "server": "proxy.example.com",
            "username": "user",
            "password": "pass",
            "port": 8080
        }
        url = proxy_manager._format_proxy_url(proxy)
        self.assertEqual(url, "http://user:pass@proxy.example.com:8080")
        
        # Тест без учетных данных
        proxy = {
            "server": "proxy.example.com",
            "port": 8080
        }
        url = proxy_manager._format_proxy_url(proxy)
        self.assertEqual(url, "http://proxy.example.com:8080")
        
        # Тест с пустым словарем
        proxy = {}
        url = proxy_manager._format_proxy_url(proxy)
        self.assertEqual(url, "")
    
    def test_get_next_proxy(self):
        """Тест получения следующего прокси."""
        # Создаем экземпляр ProxyManager с мокированным списком прокси
        proxy_manager = ProxyManager()
        proxy_manager.proxies = self.test_proxies
        proxy_manager.working_proxies = self.test_proxies
        
        # Получаем первый прокси
        proxy1 = proxy_manager.get_next_proxy()
        self.assertEqual(proxy1, self.test_proxies[0])
        
        # Получаем второй прокси
        proxy2 = proxy_manager.get_next_proxy()
        self.assertEqual(proxy2, self.test_proxies[1])
        
        # Получаем следующий прокси (должен быть снова первый)
        proxy3 = proxy_manager.get_next_proxy()
        self.assertEqual(proxy3, self.test_proxies[0])
    
    def test_get_random_proxy(self):
        """Тест получения случайного прокси."""
        # Создаем экземпляр ProxyManager с мокированным списком прокси
        proxy_manager = ProxyManager()
        proxy_manager.proxies = self.test_proxies
        proxy_manager.working_proxies = self.test_proxies
        
        # Получаем случайный прокси
        proxy = proxy_manager.get_random_proxy()
        
        # Проверяем, что прокси из списка
        self.assertIn(proxy, self.test_proxies)


class TestDataExtractor(unittest.TestCase):
    """Тесты для экстрактора данных."""
    
    def test_parse_date(self):
        """Тест парсинга даты."""
        extractor = DataExtractor()
        
        # Тест с форматом ISO
        date = extractor.parse_date("2023-01-31")
        self.assertEqual(date.year, 2023)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.day, 31)
        
        # Тест с форматом DD.MM.YYYY
        date = extractor.parse_date("31.01.2023")
        self.assertEqual(date.year, 2023)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.day, 31)
        
        # Тест с форматом DD/MM/YYYY
        date = extractor.parse_date("31/01/2023")
        self.assertEqual(date.year, 2023)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.day, 31)
        
        # Тест с неверным форматом
        date = extractor.parse_date("invalid")
        self.assertIsNone(date)
    
    def test_parse_time(self):
        """Тест парсинга времени."""
        extractor = DataExtractor()
        
        # Тест с форматом HH:MM:SS
        time = extractor.parse_time("15:30:00")
        self.assertEqual(time.hour, 15)
        self.assertEqual(time.minute, 30)
        self.assertEqual(time.second, 0)
        
        # Тест с форматом HH:MM
        time = extractor.parse_time("15:30")
        self.assertEqual(time.hour, 15)
        self.assertEqual(time.minute, 30)
        self.assertEqual(time.second, 0)
        
        # Тест с форматом HH.MM
        time = extractor.parse_time("15.30")
        self.assertEqual(time.hour, 15)
        self.assertEqual(time.minute, 30)
        self.assertEqual(time.second, 0)
        
        # Тест с форматом HH:MM AM/PM
        time = extractor.parse_time("3:30 PM")
        self.assertEqual(time.hour, 15)
        self.assertEqual(time.minute, 30)
        self.assertEqual(time.second, 0)
        
        # Тест с неверным форматом
        time = extractor.parse_time("invalid")
        self.assertIsNone(time)
    
    def test_clean_price(self):
        """Тест очистки цены."""
        extractor = DataExtractor()
        
        # Тест с числом и валютой
        price = extractor.clean_price("1000 руб")
        self.assertEqual(price, "1000 руб")
        
        # Тест с разделителем тысяч
        price = extractor.clean_price("1 000 ₽")
        self.assertEqual(price, "1000 ₽")
        
        # Тест с десятичной точкой
        price = extractor.clean_price("1000.50 руб")
        self.assertEqual(price, "1000.50 руб")
        
        # Тест с десятичной запятой
        price = extractor.clean_price("1000,50 руб")
        self.assertEqual(price, "1000,50 руб")
        
        # Тест с текстом до и после цены
        price = extractor.clean_price("Цена: 1000 руб.")
        self.assertEqual(price, "1000 руб")
    
    def test_extract_seat_number(self):
        """Тест извлечения номера места."""
        extractor = DataExtractor()
        
        # Тест с явным указанием места
        seat = extractor.extract_seat_number("Корт #5")
        self.assertEqual(seat, "5")
        
        # Тест с указанием места в тексте
        seat = extractor.extract_seat_number("Забронировать место 10")
        self.assertEqual(seat, "10")
        
        # Тест с разными вариациями написания
        seat = extractor.extract_seat_number("Зал № 3")
        self.assertEqual(seat, "3")
        
        # Тест с комнатой
        seat = extractor.extract_seat_number("Комната 7")
        self.assertEqual(seat, "7")
        
        # Тест с английским вариантом
        seat = extractor.extract_seat_number("Court #2")
        self.assertEqual(seat, "2")
        
        # Тест с просто числом
        seat = extractor.extract_seat_number("15")
        self.assertEqual(seat, "15")
        
        # Тест с несколькими числами (должен вернуть первое)
        seat = extractor.extract_seat_number("Корт 1, Место 2")
        self.assertEqual(seat, "1")


class TestYClientsParser(unittest.TestCase):
    """Тесты для основного класса парсера."""
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Тест инициализации парсера."""
        # Создаем моки
        mock_db_manager = MagicMock()
        mock_browser_manager = MagicMock()
        mock_proxy_manager = MagicMock()
        
        # Мокаем асинхронные методы
        mock_browser = MagicMock(spec=Browser)
        mock_context = MagicMock(spec=BrowserContext)
        mock_browser_manager.initialize_browser = AsyncMock(return_value=(mock_browser, mock_context))
        mock_proxy_manager.get_next_proxy = MagicMock(return_value={"server": "proxy.example.com"})
        
        # Создаем экземпляр YClientsParser
        with patch('src.parser.yclients_parser.BrowserManager', return_value=mock_browser_manager), \
             patch('src.parser.yclients_parser.ProxyManager', return_value=mock_proxy_manager):
            parser = YClientsParser(["https://example.com"], mock_db_manager)
            
            # Вызываем тестируемый метод
            await parser.initialize()
            
            # Проверяем, что методы были вызваны
            mock_proxy_manager.get_next_proxy.assert_called_once()
            mock_browser_manager.initialize_browser.assert_called_once()
            
            # Проверяем, что атрибуты установлены
            self.assertEqual(parser.browser, mock_browser)
            self.assertEqual(parser.context, mock_context)
            self.assertEqual(parser.current_proxy, {"server": "proxy.example.com"})
    
    @pytest.mark.asyncio
    async def test_close(self):
        """Тест закрытия парсера."""
        # Создаем моки
        mock_db_manager = MagicMock()
        mock_browser = MagicMock(spec=Browser)
        mock_context = MagicMock(spec=BrowserContext)
        
        # Мокаем асинхронные методы
        mock_browser.close = AsyncMock()
        mock_context.close = AsyncMock()
        
        # Создаем экземпляр YClientsParser
        parser = YClientsParser(["https://example.com"], mock_db_manager)
        parser.browser = mock_browser
        parser.context = mock_context
        
        # Вызываем тестируемый метод
        await parser.close()
        
        # Проверяем, что методы были вызваны
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
