"""
Improved YClients Parser - Исправленная версия для решения проблем с URL и парсингом.
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError

from src.browser.browser_manager import BrowserManager
from src.browser.proxy_manager import ProxyManager
from src.database.db_manager import DatabaseManager
from src.parser.improved_data_extractor import ImprovedDataExtractor
from src.parser.selectors import SELECTORS
from config.settings import PARSE_INTERVAL, MAX_RETRIES, TIMEOUT, USER_AGENTS, PAGE_LOAD_TIMEOUT


logger = logging.getLogger(__name__)


class ImprovedYClientsParser:
    """
    Улучшенный класс парсера YClients с исправлениями основных проблем.
    """

    def __init__(self, urls: List[str], db_manager: DatabaseManager):
        """Инициализация парсера."""
        self.urls = urls
        self.db_manager = db_manager
        self.browser_manager = BrowserManager()
        self.proxy_manager = ProxyManager()
        # Используем улучшенный экстрактор данных
        self.data_extractor = ImprovedDataExtractor()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.current_proxy = None
        self.retry_count = 0

    async def initialize(self) -> None:
        """Инициализация браузера и контекста."""
        try:
            logger.info("Инициализация браузера")
            self.current_proxy = self.proxy_manager.get_next_proxy()
            self.browser, self.context = await self.browser_manager.initialize_browser(
                proxy=self.current_proxy
            )
            logger.info("Браузер успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации браузера: {str(e)}")
            raise

    async def close(self) -> None:
        """Закрытие браузера и освобождение ресурсов."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("Браузер и контекст закрыты")
        except Exception as e:
            logger.error(f"Ошибка при закрытии браузера: {str(e)}")
