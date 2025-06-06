"""
Browser Manager - Управление браузером Playwright с функциями анти-обнаружения.

Этот модуль предоставляет функциональность для:
1. Инициализации браузера с настройками стелс-режима
2. Эмуляции поведения пользователя
3. Обхода базовых методов обнаружения ботов
"""
import asyncio
import logging
import random
from typing import Dict, Tuple, Optional, List, Any

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from config.settings import USER_AGENTS, VIEWPORT_SIZES, BROWSER_ARGS
from src.browser.stealth_config import apply_stealth_settings


logger = logging.getLogger(__name__)


class BrowserManager:
    """
    Управление браузером Playwright для парсинга с эмуляцией человеческого поведения.
    """

    def __init__(self):
        """Инициализация менеджера браузера."""
        self.playwright: Optional[Playwright] = None
        self.user_agents = USER_AGENTS
        self.viewport_sizes = VIEWPORT_SIZES
        self.browser_args = BROWSER_ARGS

    async def initialize_browser(self, proxy: Optional[Dict[str, str]] = None) -> Tuple[Browser, BrowserContext]:
        """
        Инициализация браузера Playwright с настройками для обхода обнаружения.
        
        Args:
            proxy: Опциональный словарь с настройками прокси
            
        Returns:
            Tuple[Browser, BrowserContext]: Браузер и контекст браузера
        """
        try:
            self.playwright = await async_playwright().start()
            
            # Настройки для браузера
            browser_args = self.browser_args.copy()
            
            # Выбираем случайный User-Agent и размер окна
            user_agent = self.get_random_user_agent()
            viewport = self.get_random_viewport()
            
            browser_kwargs = {
                "headless": True,  # В реальном проекте может быть True для скрытой работы
                "args": browser_args
            }
            
            # Создаем браузер
            browser = await self.playwright.chromium.launch(**browser_kwargs)
            
            # Настройки контекста браузера
            context_settings = {
                "viewport": viewport,
                "user_agent": user_agent,
                "bypass_csp": True,  # Обход политики безопасности контента
                "java_script_enabled": True,
                "locale": "ru-RU",
                "timezone_id": "Europe/Moscow",
                "geolocation": {"longitude": 37.6156, "latitude": 55.7522},  # Москва
                "permissions": ["geolocation"],
                "color_scheme": "light",
                "reduced_motion": "no-preference",
                "accept_downloads": True,
                "ignore_https_errors": True
            }
            
            # Добавляем настройки прокси, если они предоставлены
            if proxy:
                context_settings["proxy"] = proxy
            
            # Создаем контекст
            context = await browser.new_context(**context_settings)
            
            # Применяем настройки для обхода обнаружения ботов
            await apply_stealth_settings(context)
            
            # Настройка обработчиков событий
            await self._setup_event_handlers(context)
            
            logger.info(f"Браузер инициализирован с User-Agent: {user_agent[:30]}...")
            return browser, context
        
        except Exception as e:
            logger.error(f"Ошибка при инициализации браузера: {str(e)}")
            if self.playwright:
                await self.playwright.stop()
            raise

    def get_random_user_agent(self) -> str:
        """
        Получение случайного User-Agent из списка.
        
        Returns:
            str: Случайный User-Agent
        """
        return random.choice(self.user_agents)

    def get_random_viewport(self) -> Dict[str, int]:
        """
        Получение случайного размера окна из списка.
        
        Returns:
            Dict[str, int]: Размер окна (ширина и высота)
        """
        return random.choice(self.viewport_sizes)

    async def _setup_event_handlers(self, context: BrowserContext) -> None:
        """
        Настройка обработчиков событий для контекста браузера.
        
        Args:
            context: Контекст браузера
        """
        # Обработка JavaScript диалогов (alert, confirm, prompt)
        context.on("dialog", lambda dialog: asyncio.create_task(self._handle_dialog(dialog)))
        
        # Обработка запросов к ресурсам
        # context.route("**/*", lambda route, request: asyncio.create_task(self._handle_request(route, request)))
        
        # Обработка ошибок страницы
        context.on("page", lambda page: page.on("pageerror", lambda error: logger.error(f"Ошибка на странице: {error}")))

    async def _handle_dialog(self, dialog) -> None:
        """
        Обработка JavaScript диалогов.
        
        Args:
            dialog: Диалоговое окно
        """
        logger.info(f"Обработка диалога типа {dialog.type}: {dialog.message}")
        
        # Для большинства диалогов просто принимаем
        await dialog.accept()

    async def _handle_request(self, route, request) -> None:
        """
        Обработка запросов ресурсов.
        
        Args:
            route: Маршрут запроса
            request: Запрос
        """
        # Здесь можно фильтровать запросы, блокировать аналитику и т.д.
        # Например, блокировать запросы к трекерам
        blocked_domains = [
            "google-analytics.com",
            "analytics",
            "tracker",
            "metrics"
        ]
        
        if any(domain in request.url.lower() for domain in blocked_domains):
            logger.debug(f"Блокировка запроса к: {request.url}")
            await route.abort()
        else:
            await route.continue_()

    def get_random_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0) -> float:
        """
        Генерирует случайную задержку для эмуляции человеческого поведения.
        
        Args:
            min_seconds: Минимальное время в секундах
            max_seconds: Максимальное время в секундах
            
        Returns:
            float: Случайное время в секундах
        """
        return min_seconds + random.random() * (max_seconds - min_seconds)

    async def emulate_human_scrolling(self, page: Page) -> None:
        """
        Эмуляция человеческого скроллинга страницы.
        
        Args:
            page: Страница браузера
        """
        try:
            # Получаем высоту страницы
            page_height = await page.evaluate("document.body.scrollHeight")
            viewport_height = await page.evaluate("window.innerHeight")
            
            # Количество прокруток
            scrolls = random.randint(2, 5)
            
            for _ in range(scrolls):
                # Случайное расстояние для прокрутки
                scroll_distance = random.randint(viewport_height // 2, viewport_height)
                
                # Прокручиваем страницу
                await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
                
                # Случайная задержка между прокрутками
                await asyncio.sleep(self.get_random_delay(0.5, 1.5))
                
                # Иногда прокручиваем немного назад для естественности
                if random.random() > 0.7:
                    back_scroll = random.randint(50, 200)
                    await page.evaluate(f"window.scrollBy(0, -{back_scroll})")
                    await asyncio.sleep(self.get_random_delay(0.2, 0.7))
            
            # Иногда делаем прокрутку в самый низ страницы
            if random.random() > 0.5:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(self.get_random_delay(1.0, 2.0))
                
                # И затем возвращаемся обратно наверх
                await page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(self.get_random_delay(0.5, 1.0))
        
        except Exception as e:
            logger.error(f"Ошибка при эмуляции скроллинга: {str(e)}")

    async def emulate_mouse_movement(self, page: Page) -> None:
        """
        Эмуляция движения мыши.
        
        Args:
            page: Страница браузера
        """
        try:
            # Получаем размеры окна
            viewport_width = await page.evaluate("window.innerWidth")
            viewport_height = await page.evaluate("window.innerHeight")
            
            # Несколько случайных движений мыши
            movements = random.randint(3, 7)
            
            current_x, current_y = viewport_width // 2, viewport_height // 2
            
            for _ in range(movements):
                # Генерируем случайную целевую позицию
                target_x = random.randint(10, viewport_width - 10)
                target_y = random.randint(10, viewport_height - 10)
                
                # Перемещаем мышь
                await page.mouse.move(target_x, target_y)
                
                # Случайная задержка
                await asyncio.sleep(self.get_random_delay(0.1, 0.5))
        
        except Exception as e:
            logger.error(f"Ошибка при эмуляции движения мыши: {str(e)}")

    async def emulate_random_clicks(self, page: Page) -> None:
        """
        Эмуляция случайных кликов на неактивных элементах страницы.
        
        Args:
            page: Страница браузера
        """
        try:
            # Находим безопасные элементы для клика (например, пустые div, span)
            safe_elements = await page.query_selector_all('div:not(a):not(button):not(input), span:not(a):not(button)')
            
            if not safe_elements or len(safe_elements) == 0:
                return
            
            # Выбираем несколько случайных элементов
            num_clicks = random.randint(1, 3)
            for _ in range(num_clicks):
                element = random.choice(safe_elements)
                
                # Получаем координаты элемента
                bounding_box = await element.bounding_box()
                if bounding_box:
                    x = bounding_box["x"] + bounding_box["width"] // 2
                    y = bounding_box["y"] + bounding_box["height"] // 2
                    
                    # Кликаем на элемент
                    await page.mouse.click(x, y)
                    
                    # Случайная задержка
                    await asyncio.sleep(self.get_random_delay(0.5, 1.0))
        
        except Exception as e:
            logger.error(f"Ошибка при эмуляции случайных кликов: {str(e)}")

    async def emulate_human_behavior(self, page: Page) -> None:
        """
        Комплексная эмуляция человеческого поведения.
        
        Args:
            page: Страница браузера
        """
        try:
            # Эмуляция скроллинга
            await self.emulate_human_scrolling(page)
            
            # Эмуляция движения мыши
            await self.emulate_mouse_movement(page)
            
            # Иногда делаем случайные клики
            if random.random() > 0.7:
                await self.emulate_random_clicks(page)
            
            # Случайная задержка после всех действий
            await asyncio.sleep(self.get_random_delay(1.0, 3.0))
        
        except Exception as e:
            logger.error(f"Ошибка при эмуляции человеческого поведения: {str(e)}")
