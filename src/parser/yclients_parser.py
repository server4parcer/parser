"""
YCLIENTS Parser - Основной модуль парсинга данных с платформы YCLIENTS.
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError
import re

from src.browser.browser_manager import BrowserManager
from src.browser.proxy_manager import ProxyManager
from src.database.db_manager import DatabaseManager
from src.parser.production_data_extractor import ProductionDataExtractor
from src.parser.yclients_real_selectors import YCLIENTS_REAL_SELECTORS
from config.settings import PARSE_INTERVAL, MAX_RETRIES, TIMEOUT, USER_AGENTS, PAGE_LOAD_TIMEOUT


logger = logging.getLogger(__name__)


class YClientsParser:
    """
    Основной класс для парсинга данных с YCLIENTS.
    Использует Playwright для работы с веб-страницами и эмуляции поведения пользователя.
    """

    def __init__(self, urls: List[str], db_manager: DatabaseManager):
        """
        Инициализация парсера.
        
        Args:
            urls: Список URL-адресов для парсинга
            db_manager: Экземпляр менеджера базы данных
        """
        self.urls = urls
        self.db_manager = db_manager
        self.browser_manager = BrowserManager()
        self.proxy_manager = ProxyManager()
        # Используем production-ready экстрактор данных
        self.data_extractor = ProductionDataExtractor()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.current_proxy = None
        self.retry_count = 0
        self.last_parsed_urls = {}  # Для отслеживания успешно обработанных URL

    async def initialize(self) -> None:
        """Инициализация браузера и контекста."""
        try:
            logger.info("Инициализация браузера")
            
            # Получаем прокси для текущей сессии
            self.current_proxy = self.proxy_manager.get_next_proxy()
            
            # Инициализируем браузер с настройками стелс-режима
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

    async def navigate_to_url(self, url: str) -> bool:
        """
        Переход по URL с обработкой ошибок и повторными попытками.
        
        Args:
            url: URL страницы для загрузки
            
        Returns:
            bool: True если переход успешен, False в противном случае
        """
        try:
            # Создаем новую страницу в текущем контексте
            self.page = await self.context.new_page()
            
            # Устанавливаем случайный юзер-агент из списка доступных
            user_agent = self.browser_manager.get_random_user_agent()
            await self.page.set_extra_http_headers({"User-Agent": user_agent})
            
            # Эмуляция поведения пользователя: случайные задержки перед навигацией
            await asyncio.sleep(self.browser_manager.get_random_delay(1, 3))
            
            logger.info(f"Переход по URL: {url}")
            
            # Устанавливаем таймаут загрузки страницы
            response = await self.page.goto(
                url, 
                timeout=PAGE_LOAD_TIMEOUT,
                wait_until="networkidle"
            )
            
            if not response or response.status >= 400:
                logger.error(f"Неудачный запрос к {url}, статус: {response.status if response else 'unknown'}")
                return False
            
            # Ждем полной загрузки страницы и динамического контента
            await self.page.wait_for_load_state("networkidle")
            
            # Эмуляция случайного скроллинга страницы
            await self.browser_manager.emulate_human_scrolling(self.page)
            
            return True
            
        except TimeoutError:
            logger.error(f"Таймаут при загрузке страницы: {url}")
            return False
        except Exception as e:
            logger.error(f"Ошибка при навигации на {url}: {str(e)}")
            return False

    async def handle_service_selection_page(self, url: str) -> List[str]:
        """
        Обработка страницы выбора услуг для получения прямых ссылок на бронирование.
        Решает проблему редиректа с URL типа record-type?o=
        
        Args:
            url: URL страницы выбора услуг
            
        Returns:
            List[str]: Список прямых URL для бронирования конкретных услуг
        """
        logger.info(f"Обработка страницы выбора услуг: {url}")
        direct_urls = []
        
        try:
            # Переходим на страницу выбора услуг
            navigation_success = await self.navigate_to_url(url)
            if not navigation_success:
                logger.error(f"Не удалось загрузить страницу выбора услуг: {url}")
                return []
            
            # Ждем загрузки списка услуг
            try:
                await self.page.wait_for_selector('.service-item, .service-option, .record__service', timeout=10000)
            except Exception:
                logger.warning("Не удалось дождаться загрузки списка услуг")
                return []
            
            # Получаем все доступные услуги
            service_selectors = [
                '.service-item', '.service-option', '.record__service',
                '.ycwidget-service', '.booking-service-item'
            ]
            
            service_elements = []
            for selector in service_selectors:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    service_elements = elements
                    logger.info(f"Найдено {len(elements)} услуг с селектором: {selector}")
                    break
            
            if not service_elements:
                logger.warning("Не найдены элементы услуг на странице")
                return []
            
            # Для каждой услуги получаем прямую ссылку
            for i, service_element in enumerate(service_elements[:5]):  # Ограничиваем количество для безопасности
                try:
                    # Пробуем найти ссылку внутри элемента
                    link_element = await service_element.query_selector('a')
                    if link_element:
                        href = await link_element.get_attribute('href')
                        if href:
                            if href.startswith('/'):
                                # Преобразуем относительную ссылку в абсолютную
                                base_url = '/'.join(url.split('/')[:3])
                                direct_url = base_url + href
                            else:
                                direct_url = href
                            
                            if 'record' in direct_url and direct_url not in direct_urls:
                                direct_urls.append(direct_url)
                                logger.info(f"Найдена прямая ссылка: {direct_url}")
                                continue
                    
                    # Если ссылки нет, пробуем кликнуть на элемент
                    logger.info(f"Кликаем на услугу {i+1}")
                    await service_element.click()
                    await asyncio.sleep(2)  # Ждем навигации
                    
                    # Получаем URL после клика
                    current_url = self.page.url
                    if 'record' in current_url and current_url != url and current_url not in direct_urls:
                        direct_urls.append(current_url)
                        logger.info(f"Получена ссылка после клика: {current_url}")
                    
                    # Возвращаемся на страницу выбора услуг
                    await self.page.go_back()
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.warning(f"Ошибка при обработке услуги {i+1}: {str(e)}")
                    continue
            
            logger.info(f"Получено {len(direct_urls)} прямых ссылок для бронирования")
            return direct_urls
            
        except Exception as e:
            logger.error(f"Ошибка при обработке страницы выбора услуг: {str(e)}")
            return []

    async def check_for_antibot(self) -> bool:
        """
        Проверка наличия антибот-защиты и её обход, если возможно.
        
        Returns:
            bool: True если защиты нет или она успешно обойдена, False в противном случае
        """
        try:
            # Проверка на наличие капчи или других форм защиты
            captcha_exists = await self.page.query_selector(".captcha, .recaptcha, .hcaptcha")
            if captcha_exists:
                logger.warning("Обнаружена CAPTCHA, попытка обхода...")
                # Здесь могла бы быть реализация обхода капчи
                # В данной реализации просто закрываем страницу и меняем прокси
                return False
            
            # Проверка на блокировку IP
            blocked_ip = await self.page.query_selector(".blocked, .access-denied, .error-403")
            if blocked_ip:
                logger.warning("IP заблокирован, смена прокси")
                return False
                
            # Другие проверки на антибот-защиту...
            
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке антибот-защиты: {str(e)}")
            return False

    async def navigate_yclients_flow(self, page: Page, url: str) -> List[Dict]:
        """
        Navigate through YClients 4-step booking flow.
        Step 1: Service selection (record-type)
        Step 2: Court selection (select-master)
        Step 3: Date/time selection (select-time)
        Step 4: Service packages with prices (select-services)
        """
        results = []
        
        try:
            # Step 1: Load and select service type
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_selector('ui-kit-simple-cell', timeout=10000)
            
            # Click on "Индивидуальные услуги" or first available service
            service_links = await page.get_by_role('link').all()
            for link in service_links:
                text = await link.text_content()
                if 'Индивидуальные' in text or 'услуги' in text.lower():
                    await link.click()
                    break
            
            # Step 2: Select courts
            await page.wait_for_url('**/personal/select-master**')
            await page.wait_for_selector('ui-kit-simple-cell')
            
            courts = await page.locator('ui-kit-simple-cell').all()
            for court in courts[:3]:  # Limit to first 3 courts for testing
                court_name = await court.locator('ui-kit-headline').text_content()
                await court.click()
                
                # Continue to date selection
                continue_btn = page.get_by_role('button', { 'name': 'Продолжить' })
                if await continue_btn.is_visible():
                    await continue_btn.click()
                
                # Step 3: Select dates and times
                await page.wait_for_url('**/personal/select-time**')
                await self.extract_time_slots_with_prices(page, court_name, results)
                
                # Go back to court selection
                await page.go_back()
                await page.wait_for_selector('ui-kit-simple-cell')
        
        except Exception as e:
            logger.error(f"Error in 4-step navigation: {str(e)}")
        
        return results

    async def extract_time_slots_with_prices(self, page: Page, court_name: str, results: List[Dict]):
        """Extract time slots and navigate to get prices."""
        
        try:
            # Get available dates
            dates = await page.locator('.calendar-day:not(.disabled)').all()
            
            for date in dates[:2]:  # Limit to 2 dates for testing
                date_text = await date.text_content()
                await date.click()
                await page.wait_for_timeout(1000)
                
                # Get time slots
                time_slots = await page.locator('[data-time]').all()
                if not time_slots:
                    # Try alternative selector
                    time_slots = await page.get_by_text(re.compile(r'\d{1,2}:\d{2}')).all()
                
                for slot in time_slots[:3]:  # Limit to 3 slots per date
                    time_text = await slot.text_content()
                    await slot.click()
                    
                    # Continue to services/prices
                    continue_btn = page.get_by_role('button', { 'name': 'Продолжить' })
                    if await continue_btn.is_visible():
                        await continue_btn.click()
                        
                        # Step 4: Extract prices from service packages
                        await page.wait_for_url('**/personal/select-services**')
                        await page.wait_for_selector('ui-kit-simple-cell')
                        
                        services = await page.locator('ui-kit-simple-cell').all()
                        for service in services:
                            try:
                                name = await service.locator('ui-kit-headline').text_content()
                                price = await service.locator('ui-kit-title').text_content()
                                duration = await service.locator('ui-kit-body').text_content()
                                
                                # Clean and structure data
                                result = {
                                    'url': page.url,
                                    'court_name': court_name.strip() if court_name else '',
                                    'date': self.parse_date(date_text),
                                    'time': time_text.strip() if time_text else '',
                                    'service_name': name.strip() if name else '',
                                    'price': self.clean_price(price),
                                    'duration': self.parse_duration(duration),
                                    'venue_name': self.extract_venue_name(page.url),
                                    'extracted_at': datetime.now().isoformat()
                                }
                                results.append(result)
                            except Exception as e:
                                logger.warning(f"Failed to extract service: {e}")
                        
                        # Go back to time selection
                        await page.go_back()
                        await page.wait_for_timeout(1000)
        except Exception as e:
            logger.error(f"Error extracting time slots with prices: {str(e)}")

    def clean_price(self, price_text: str) -> str:
        """Clean price text: '6,000 ₽' -> '6000 ₽'"""
        if not price_text:
            return "Цена не указана"
        # Remove spaces and commas from numbers
        cleaned = re.sub(r'(\d),(\d)', r'\1\2', price_text)
        cleaned = re.sub(r'(\d)\s+(\d)', r'\1\2', cleaned)
        cleaned = cleaned.strip()
        return cleaned if '₽' in cleaned or 'руб' in cleaned else f"{cleaned} ₽"

    def parse_duration(self, duration_text: str) -> int:
        """Parse duration: '1 ч 30 мин' -> 90"""
        if not duration_text:
            return 60
        
        total_minutes = 0
        # Extract hours
        hour_match = re.search(r'(\d+)\s*ч', duration_text)
        if hour_match:
            total_minutes += int(hour_match.group(1)) * 60
        
        # Extract minutes
        min_match = re.search(r'(\d+)\s*мин', duration_text)
        if min_match:
            total_minutes += int(min_match.group(1))
        
        return total_minutes if total_minutes > 0 else 60

    def parse_date(self, date_text: str) -> str:
        """Parse date from calendar text to ISO format."""
        # For now, return current date. Can be enhanced with proper date parsing
        # Russian month mapping
        months = {
            'январ': '01', 'феврал': '02', 'март': '03', 'апрел': '04',
            'май': '05', 'май': '05', 'июн': '06', 'июл': '07',
            'август': '08', 'сентябр': '09', 'октябр': '10',
            'ноябр': '11', 'декабр': '12'
        }
        
        try:
            # Try to extract day and month
            day_match = re.search(r'(\d{1,2})', date_text)
            if day_match:
                day = day_match.group(1).zfill(2)
                # Find month
                for month_name, month_num in months.items():
                    if month_name in date_text.lower():
                        year = datetime.now().year
                        return f"{year}-{month_num}-{day}"
        except:
            pass
        
        return datetime.now().strftime('%Y-%m-%d')

    def extract_venue_name(self, url: str) -> str:
        """Extract venue name from URL or page content."""
        # This is a placeholder - actual implementation would extract from page
        if 'n1165596' in url:
            return 'Нагатинская'
        elif 'n1308467' in url:
            return 'Корты-Сетки'
        elif 'b861100' in url:
            return 'Padel Friends'
        elif 'b1009933' in url:
            return 'ТК Ракетлон'
        elif 'b918666' in url:
            return 'Padel A33'
        return 'Unknown Venue'

    async def extract_available_dates(self) -> List[Dict[str, Any]]:
        """
        Извлечение доступных дат бронирования.
        
        Returns:
            List[Dict[str, Any]]: Список доступных дат
        """
        logger.info("Извлечение доступных дат бронирования")
        try:
            # Ожидаем загрузки календаря
            await self.page.wait_for_selector(YCLIENTS_REAL_SELECTORS["calendar"]["calendar_container"], timeout=TIMEOUT)
            
            # Получаем элементы доступных дат
            date_elements = await self.page.query_selector_all(YCLIENTS_REAL_SELECTORS["calendar"]["available_dates"])
            
            # Извлечение данных из элементов
            available_dates = []
            for date_element in date_elements:
                # Получаем атрибуты, текст и другие данные элемента
                date_text = await date_element.text_content()
                date_attr = await date_element.get_attribute("data-date")
                
                if date_text and date_attr:
                    available_dates.append({
                        "date": date_attr,
                        "display_text": date_text.strip()
                    })
            
            logger.info(f"Найдено {len(available_dates)} доступных дат")
            return available_dates
        except Exception as e:
            logger.error(f"Ошибка при извлечении доступных дат: {str(e)}")
            return []

    async def extract_time_slots(self, date: str) -> List[Dict[str, Any]]:
        """
        Извлечение доступных временных слотов для выбранной даты.
        
        Args:
            date: Дата для выбора
            
        Returns:
            List[Dict[str, Any]]: Список доступных временных слотов
        """
        logger.info(f"Извлечение временных слотов для даты: {date}")
        try:
            # Выбираем дату в календаре
            date_selector = YCLIENTS_REAL_SELECTORS["calendar"]["date_selector"].format(date=date)
            date_element = await self.page.query_selector(date_selector)
            
            if not date_element:
                logger.warning(f"Элемент даты {date} не найден")
                return []
                
            # Кликаем на дату для загрузки доступных слотов
            await date_element.click()
            await asyncio.sleep(2)  # Ожидание загрузки слотов
            
            # Ждем появления контейнера со слотами
            await self.page.wait_for_selector(YCLIENTS_REAL_SELECTORS["time_slots"]["container"], timeout=TIMEOUT)
            
            # Получаем элементы доступных временных слотов
            slot_elements = await self.page.query_selector_all(YCLIENTS_REAL_SELECTORS["time_slots"]["slots"])
            
            time_slots = []
            for slot_element in slot_elements:
                # Определяем, является ли дата выходным днем
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                is_weekend = date_obj.weekday() >= 5  # 5 и 6 - суббота и воскресенье
                
                # Используем исправленный экстрактор данных для получения всех полей
                slot_data = await self.data_extractor.extract_slot_data_fixed(
                    slot_element
                )
                
                # Добавляем дату, если её нет
                if "date" not in slot_data:
                    slot_data["date"] = date
                    
                time_slots.append(slot_data)
            
            logger.info(f"Найдено {len(time_slots)} временных слотов для даты {date}")
            return time_slots
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении временных слотов для даты {date}: {str(e)}")
            return []

    async def parse_url(self, url: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Парсинг данных с одного URL.
        Обновлен для обработки страниц выбора услуг (record-type).
        
        Args:
            url: URL для парсинга
            
        Returns:
            Tuple[bool, List[Dict[str, Any]]]: Статус успеха и список извлеченных данных
        """
        logger.info(f"Начало парсинга URL: {url}")
        all_data = []
        success = False
        
        try:
            # Проверяем, является ли это страницей выбора услуг
            if 'record-type' in url or 'select-service' in url:
                logger.info("Обнаружена страница выбора услуг, получаем прямые ссылки")
                # Получаем прямые ссылки на услуги
                direct_urls = await self.handle_service_selection_page(url)
                
                if not direct_urls:
                    logger.warning("Не получены прямые ссылки, попробуем парсить страницу как есть")
                    # Fallback: парсим страницу как обычно
                    success, all_data = await self.parse_service_url(url)
                else:
                    # Парсим каждую услугу отдельно
                    for service_url in direct_urls:
                        logger.info(f"Парсинг услуги: {service_url}")
                        service_success, service_data = await self.parse_service_url(service_url)
                        if service_success:
                            all_data.extend(service_data)
                            success = True
                        
                        # Небольшая пауза между запросами
                        await asyncio.sleep(2)
            else:
                # Обычный парсинг прямой ссылки
                success, all_data = await self.parse_service_url(url)
            
            if success:
                self.last_parsed_urls[url] = datetime.now()
                logger.info(f"Парсинг URL: {url} завершен успешно, получено {len(all_data)} записей")
            else:
                logger.error(f"Парсинг URL: {url} завершен неудачно")
            
            return success, all_data
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге URL {url}: {str(e)}")
            return False, []

    async def parse_service_url(self, url: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Парсинг данных с прямого URL услуги.
        Обновлен для использования 4-шагового навигационного потока YClients.
        
        Args:
            url: URL для парсинга
            
        Returns:
            Tuple[bool, List[Dict[str, Any]]]: Статус успеха и список извлеченных данных
        """
        logger.info(f"Парсинг прямой ссылки услуги: {url}")
        all_data = []
        
        try:
            # Навигация на страницу
            navigation_success = await self.navigate_to_url(url)
            if not navigation_success:
                logger.error(f"Не удалось загрузить страницу: {url}")
                return False, []
                
            # Проверка на антибот-защиту
            if not await self.check_for_antibot():
                logger.warning("Обнаружена защита от ботов, смена прокси и перезапуск")
                return False, []
            
            # Проверяем, является ли это YClients URL
            if self.is_yclients_url(url):
                logger.info("🎯 Используем 4-шаговую навигацию YClients")
                # Используем новую 4-шаговую навигацию
                all_data = await self.navigate_yclients_flow(self.page, url)
            else:
                logger.info("📄 Используем стандартное извлечение данных")
                # Извлечение доступных дат (старый метод для других сайтов)
                available_dates = await self.extract_available_dates()
                if not available_dates:
                    logger.warning("Не найдены доступные даты")
                    return False, []
                    
                # Для каждой доступной даты извлекаем временные слоты
                for date_info in available_dates:
                    date = date_info["date"]
                    
                    # Извлечение временных слотов
                    time_slots = await self.extract_time_slots(date)
                    
                    # Добавляем данные в общий список
                    all_data.extend(time_slots)
                    
                    # Имитация поведения пользователя: случайная задержка между запросами
                    await asyncio.sleep(self.browser_manager.get_random_delay(1, 3))
            
            success = len(all_data) > 0
            if success:
                self.last_parsed_urls[url] = datetime.now()
                logger.info(f"Парсинг URL: {url} завершен успешно, получено {len(all_data)} записей")
            else:
                logger.warning(f"Парсинг URL: {url} завершен, но данные не извлечены")
                
            return success, all_data
        
        except Exception as e:
            logger.error(f"Ошибка при парсинге прямой ссылки {url}: {str(e)}")
            return False, []
    
    def is_yclients_url(self, url: str) -> bool:
        """Проверяет, является ли URL страницей YClients."""
        yclients_indicators = [
            'yclients.com',
            'record-type',
            'personal/',
            'select-time',
            'select-master'
        ]
        return any(indicator in url for indicator in yclients_indicators)

    async def parse_all_urls(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Парсинг данных со всех URL.
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: Словарь с данными для каждого URL
        """
        logger.info("Начало парсинга всех URL")
        results = {}
        
        try:
            await self.initialize()
            
            for url in self.urls:
                retry_count = 0
                success = False
                data = []
                
                # Делаем несколько попыток парсинга с разными прокси
                while not success and retry_count < MAX_RETRIES:
                    success, data = await self.parse_url(url)
                    
                    if not success:
                        retry_count += 1
                        logger.warning(f"Попытка {retry_count}/{MAX_RETRIES} для {url} не удалась, смена прокси")
                        
                        # Закрываем текущий контекст и браузер
                        await self.close()
                        
                        # Меняем прокси и инициализируем новый браузер
                        self.current_proxy = self.proxy_manager.get_next_proxy()
                        self.browser, self.context = await self.browser_manager.initialize_browser(
                            proxy=self.current_proxy
                        )
                    else:
                        # Если успешно, сохраняем данные
                        results[url] = data
                
                # Если все попытки неудачны, записываем пустой список
                if not success:
                    logger.error(f"Не удалось обработать URL {url} после {MAX_RETRIES} попыток")
                    results[url] = []
                
            logger.info(f"Парсинг всех URL завершен, обработано {len(results)} URL")
        
        except Exception as e:
            logger.error(f"Критическая ошибка при парсинге URL: {str(e)}")
        finally:
            await self.close()
        
        return results

    async def run_single_iteration(self) -> None:
        """Выполнение одной итерации парсинга всех URL."""
        logger.info("Начало итерации парсинга")
        start_time = time.time()
        
        try:
            # Получаем данные со всех URL
            results = await self.parse_all_urls()
            
            # Сохраняем полученные данные в базу данных
            for url, data in results.items():
                if data:
                    logger.info(f"Сохранение {len(data)} записей для URL {url}")
                    await self.db_manager.save_booking_data(url, data)
                else:
                    logger.warning(f"Нет данных для сохранения для URL {url}")
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении итерации парсинга: {str(e)}")
        
        elapsed_time = time.time() - start_time
        logger.info(f"Итерация парсинга завершена за {elapsed_time:.2f} секунд")

    async def run_continuous(self) -> None:
        """Непрерывный парсинг с заданным интервалом."""
        logger.info(f"Запуск непрерывного парсинга с интервалом {PARSE_INTERVAL} секунд")
        
        while True:
            try:
                await self.run_single_iteration()
                logger.info(f"Ожидание {PARSE_INTERVAL} секунд до следующей итерации")
                await asyncio.sleep(PARSE_INTERVAL)
            
            except KeyboardInterrupt:
                logger.info("Получен сигнал остановки, завершение работы")
                break
            
            except Exception as e:
                logger.error(f"Непредвиденная ошибка в цикле парсинга: {str(e)}")
                # Небольшая пауза перед следующей попыткой в случае ошибки
                await asyncio.sleep(10)


async def main():
    """Пример использования парсера."""
    from src.database.db_manager import DatabaseManager
    
    # Пример URL для парсинга
    urls = [
        "https://yclients.com/company/111111/booking",
        "https://yclients.com/company/222222/booking"
    ]
    
    # Инициализация менеджера базы данных
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    # Инициализация парсера
    parser = YClientsParser(urls, db_manager)
    
    # Запуск одной итерации парсинга
    await parser.run_single_iteration()
    
    # Закрытие соединения с базой данных
    await db_manager.close()


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Запуск основной функции
    asyncio.run(main())
