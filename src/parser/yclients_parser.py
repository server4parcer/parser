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
        self.captured_api_data = []  # Shared list for API responses captured during page navigation
        self.scraped_providers = []  # HTML-scraped provider/court names for 100% business value

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

            # ========== API REQUEST LOGGING AND CAPTURE FOR SPA ==========
            # Clear previously captured data for new page
            self.captured_api_data = []

            async def capture_and_log_api(response):
                """Capture API responses AND log them for debugging"""
                url = response.url

                # Log ALL API calls for debugging
                if any(keyword in url for keyword in ['api', 'booking', 'slot', 'availability', 'time', 'service', 'calendar', 'ajax', 'data']):
                    logger.info(f"🌐 [API-CALL] {response.status} {response.request.method} {url}")

                    # Try to capture and log response data
                    try:
                        if response.status == 200:
                            content_type = response.headers.get('content-type', '')

                            if 'application/json' in content_type:
                                data = await response.json()
                                logger.info(f"🌐 [API-DATA] JSON response keys: {list(data.keys()) if isinstance(data, dict) else 'array'}")

                                # Log sample data
                                if isinstance(data, list) and len(data) > 0:
                                    logger.info(f"🌐 [API-SAMPLE] First item: {str(data[0])[:200]}")
                                elif isinstance(data, dict):
                                    logger.info(f"🌐 [API-SAMPLE] Data: {str(data)[:200]}")

                                # Захватываем ВСЕ API для корреляции данных
                                # search-timeslots: время бронирования (datetime, time)
                                # search-services: цены и названия услуг (price_min, price_max, service_name)
                                # search-staff: имена мастеров/кортов (staff_name)
                                # search-dates: доступные даты
                                if any(keyword in url for keyword in [
                                    'search-timeslots',   # Время бронирования
                                    'search-services',    # Цены и названия услуг
                                    'search-staff',       # Провайдеры/корты
                                    'search-dates',       # Доступные даты
                                ]):
                                    # Identify API type
                                    api_type = 'UNKNOWN'
                                    if 'search-timeslots' in url:
                                        api_type = 'TIMESLOTS'
                                    elif 'search-services' in url:
                                        api_type = 'SERVICES'
                                    elif 'search-staff' in url:
                                        api_type = 'STAFF'
                                    elif 'search-dates' in url:
                                        api_type = 'DATES'

                                    logger.info(f"🌐 [API-CAPTURE] ✅ Captured {api_type} from: {url}")

                                    # Log data structure details
                                    if isinstance(data, dict) and 'data' in data:
                                        items = data['data'] if isinstance(data['data'], list) else [data['data']]
                                        logger.info(f"🌐 [API-CAPTURE] {api_type} has {len(items)} items")
                                        if items and len(items) > 0:
                                            first_item = items[0]
                                            if isinstance(first_item, dict) and 'attributes' in first_item:
                                                attrs = first_item['attributes']
                                                logger.info(f"🌐 [API-CAPTURE] {api_type} first item keys: {list(attrs.keys())}")

                                    self.captured_api_data.append({
                                        'api_url': url,
                                        'data': data,
                                        'timestamp': datetime.now().isoformat()
                                    })
                    except Exception as e:
                        logger.debug(f"Could not parse API response: {e}")

            # Attach listener to page
            self.page.on('response', capture_and_log_api)
            logger.info("🌐 [INIT] Network request listener attached (with capture)")
            # ========== END API REQUEST LOGGING AND CAPTURE ==========

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

            # ========== HTML PROVIDER SCRAPING FOR 100% BUSINESS VALUE ==========
            # Scrape provider/court names from HTML (APIs don't have them!)
            await self.scrape_provider_names_from_html()
            # ========== END HTML PROVIDER SCRAPING ==========

            return True
            
        except TimeoutError:
            logger.error(f"Таймаут при загрузке страницы: {url}")
            return False
        except Exception as e:
            logger.error(f"Ошибка при навигации на {url}: {str(e)}")
            return False

    async def scrape_provider_names_from_html(self) -> None:
        """
        Scrape provider/court names from HTML page.
        CRITICAL FOR 100% BUSINESS VALUE - APIs don't have service_name/provider fields!

        Strategy:
        - Find all service/court name elements in DOM
        - Extract text + associated data-id/service-id attributes
        - Store for later correlation with API data
        """
        try:
            logger.info("🏷️  [HTML-SCRAPE] Starting provider name extraction from HTML")

            # Clear previous scraped data
            self.scraped_providers = []

            # Wait a bit for dynamic content to fully render
            await asyncio.sleep(1)

            # Execute JavaScript to find all provider/court/service name elements
            providers = await self.page.evaluate('''() => {
                const results = [];

                // Try multiple selector strategies
                const selectors = [
                    // YClients common patterns
                    '.service-name',
                    '.service-title',
                    '.service-card .title',
                    '.service-item .name',
                    '.staff-name',
                    '.staff-title',
                    '.court-name',
                    '.booking-service-name',
                    '[data-service-name]',
                    '[data-court-name]',
                    '[data-service-title]',
                    // Generic patterns
                    '.service h3',
                    '.service h4',
                    '.card-title',
                    '.item-title',
                    // Try data attributes
                    '[data-service-id]',
                    '[data-staff-id]',
                    '[data-id][class*="service"]',
                    '[data-id][class*="court"]'
                ];

                for (const selector of selectors) {
                    try {
                        const elements = document.querySelectorAll(selector);
                        for (const el of elements) {
                            const text = el.textContent?.trim();
                            if (text && text.length > 0 && text.length < 200) {
                                const id = el.dataset.serviceId || el.dataset.staffId ||
                                           el.dataset.id || el.dataset.courtId ||
                                           el.getAttribute('data-service-id') ||
                                           el.getAttribute('data-id');

                                // Only add if we haven't seen this text yet
                                if (!results.some(r => r.name === text)) {
                                    results.push({
                                        name: text,
                                        id: id || null,
                                        selector: selector,
                                        className: el.className
                                    });
                                }
                            }
                        }
                    } catch (e) {
                        // Selector failed, continue
                    }
                }

                return results;
            }''')

            self.scraped_providers = providers

            if providers:
                logger.info(f"🏷️  [HTML-SCRAPE] Found {len(providers)} provider/court names:")
                for provider in providers[:5]:  # Log first 5
                    logger.info(f"   - {provider.get('name')} (id: {provider.get('id')}, selector: {provider.get('selector')})")
                if len(providers) > 5:
                    logger.info(f"   ... and {len(providers) - 5} more")
            else:
                logger.warning("🏷️  [HTML-SCRAPE] No provider names found in HTML (may need manual selector inspection)")

        except Exception as e:
            logger.error(f"🏷️  [HTML-SCRAPE] Error scraping providers: {e}")
            self.scraped_providers = []

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

    async def extract_via_api_interception(self, page: Page, url: str) -> List[Dict]:
        """
        Extract booking data by capturing API responses instead of DOM scraping.
        This works for SPA (Single Page Applications) like YClients that load data via JavaScript.

        Args:
            page: Playwright page object
            url: URL to navigate and extract from

        Returns:
            List of extracted booking records
        """
        logger.info("🌐 [API-MODE] Starting API-based extraction")

        try:
            # Use data that was ALREADY captured during page load by the main listener
            # Page is already loaded, wait for any pending API calls to complete
            await page.wait_for_timeout(2000)
            await page.wait_for_load_state('networkidle', timeout=10000)

            # Check if we already have captured data from navigation
            initial_count = len(self.captured_api_data)
            logger.info(f"🌐 [API-MODE] Already captured {initial_count} API responses during page load")

            # Try to interact with page to trigger MORE API calls (if needed)
            # Click any visible date elements to load time slots
            try:
                dates = await page.locator('.calendar-day:not(.disabled)').all()
                if dates and len(dates) > 0:
                    logger.info(f"🌐 [API-MODE] Found {len(dates)} dates, clicking first to trigger more APIs")
                    await dates[0].click(force=True)
                    await page.wait_for_timeout(2000)
                    await page.wait_for_load_state('networkidle')
            except:
                pass

            # Try clicking service items if on menu page
            try:
                services = await page.locator('[class*="service"], [class*="item"]').all()
                if services and len(services) > 0:
                    logger.info(f"🌐 [API-MODE] Found {len(services)} services, clicking first to trigger more APIs")
                    await services[0].click(force=True)
                    await page.wait_for_timeout(2000)
                    await page.wait_for_load_state('networkidle')
            except:
                pass

            # Check how many responses we have now (including new ones from clicks)
            total_captured = len(self.captured_api_data)
            logger.info(f"🌐 [API-MODE] Total captured API responses: {total_captured} ({total_captured - initial_count} new from interactions)")

            # Process ALL captured API data
            if self.captured_api_data:
                return self.parse_api_responses(self.captured_api_data)
            else:
                logger.warning("🌐 [API-MODE] No API data captured")
                return []

        except Exception as e:
            logger.error(f"🌐 [API-MODE] Error: {str(e)}")
            return []

    def parse_api_responses(self, captured_data: List[Dict]) -> List[Dict]:
        """
        Parse captured API responses into booking records.
        This method tries different response structures based on common API patterns.

        Args:
            captured_data: List of captured API responses with metadata

        Returns:
            List of parsed booking records
        """
        logger.info(f"🌐 [API-PARSE] Processing {len(captured_data)} API responses")

        results = []

        # PHASE 1: Separate data by API type for correlation
        services_data = []  # From search-services (has prices, service names)
        staff_data = []     # From search-staff (has provider/court names)
        timeslots_data = [] # From search-timeslots (has dates/times)
        dates_data = []     # From search-dates (has available dates)

        logger.info(f"🔗 [CORRELATION] Step 1: Separating {len(captured_data)} APIs by type")

        # Log all captured API URLs for debugging
        for item in captured_data:
            api_url = item['api_url']
            logger.info(f"🔗 [CORRELATION] Captured API: {api_url}")

        for item in captured_data:
            api_url = item['api_url']
            data = item['data']

            try:
                # Extract items from JSON API format
                items = []
                if isinstance(data, dict) and 'data' in data:
                    items = data['data'] if isinstance(data['data'], list) else [data['data']]
                elif isinstance(data, list):
                    items = data

                # Categorize by API type
                if 'search-services' in api_url:
                    for service in items:
                        if isinstance(service, dict) and 'attributes' in service:
                            services_data.append(service['attributes'])
                        elif isinstance(service, dict):
                            services_data.append(service)
                    logger.info(f"🔗 [CORRELATION] Found {len(items)} services from {api_url}")

                elif 'search-staff' in api_url:
                    for staff in items:
                        if isinstance(staff, dict) and 'attributes' in staff:
                            staff_data.append(staff['attributes'])
                        elif isinstance(staff, dict):
                            staff_data.append(staff)
                    logger.info(f"🔗 [CORRELATION] Found {len(items)} staff from {api_url}")

                elif 'search-timeslots' in api_url:
                    for slot in items:
                        if isinstance(slot, dict) and 'attributes' in slot:
                            timeslots_data.append(slot['attributes'])
                        elif isinstance(slot, dict):
                            timeslots_data.append(slot)
                    logger.info(f"🔗 [CORRELATION] Found {len(items)} timeslots from {api_url}")

                elif 'search-dates' in api_url:
                    for date in items:
                        if isinstance(date, dict) and 'attributes' in date:
                            dates_data.append(date['attributes'])
                        elif isinstance(date, dict):
                            dates_data.append(date)
                    logger.info(f"🔗 [CORRELATION] Found {len(items)} dates from {api_url}")

            except Exception as e:
                logger.warning(f"🔗 [CORRELATION] Failed to categorize {api_url}: {e}")

        # PHASE 2: Correlate data from different APIs
        logger.info(f"🔗 [CORRELATION] Step 2: Merging data - Services:{len(services_data)}, Staff:{len(staff_data)}, Slots:{len(timeslots_data)}")

        # Strategy: Apply service/staff data to all timeslots from same page load
        # Assumption: 1 service + N timeslots = service applies to all slots
        base_service = services_data[0] if services_data else {}
        base_staff = staff_data[0] if staff_data else {}

        if base_service:
            logger.info(f"🔗 [CORRELATION] Base service: {base_service.get('service_name', 'N/A')}, price: {base_service.get('price_min', 'N/A')}")
        if base_staff:
            logger.info(f"🔗 [CORRELATION] Base staff: {base_staff.get('staff_name', 'N/A')}")

        # Deduplication: Track seen records by (date, time, provider) composite key
        seen_records = set()

        # Merge timeslots with service/staff data + HTML-scraped providers
        for slot_data in timeslots_data:
            merged = {
                **slot_data,      # datetime, time, is_bookable
                **base_service,   # price_min, price_max, service_name, duration
                **base_staff      # staff_name
            }

            # ========== PHASE 2.5: MERGE HTML-SCRAPED PROVIDERS FOR 100% VALUE ==========
            # APIs don't have service_name, so use HTML-scraped data!
            service_id = merged.get('id') or base_service.get('id')
            provider_name = None

            if service_id and self.scraped_providers:
                # Try to match by ID
                for provider in self.scraped_providers:
                    if provider.get('id') == str(service_id):
                        provider_name = provider.get('name')
                        logger.info(f"🏷️  [CORRELATION] Matched provider by ID: {provider_name}")
                        break

            # Fallback: If no ID match, use first scraped provider (better than nothing)
            if not provider_name and self.scraped_providers:
                provider_name = self.scraped_providers[0].get('name')
                logger.info(f"🏷️  [CORRELATION] Using first scraped provider (no ID match): {provider_name}")

            # Add provider to merged data
            if provider_name:
                merged['provider'] = provider_name
            # ========== END HTML-SCRAPED PROVIDERS MERGE ==========

            logger.info(f"🔗 [CORRELATION] Merged slot: time={merged.get('time')}, price={merged.get('price_min')}, provider={merged.get('provider', 'N/A')}")
            result = self.parse_booking_from_api(merged, 'correlated-api')
            if result:
                # Deduplication check using (date, time, provider) composite key
                dedup_key = (result.get('date'), result.get('time'), result.get('provider'))

                # Only add if unique AND has date+time (provider can be None/fallback)
                if dedup_key not in seen_records and result.get('date') and result.get('time'):
                    results.append(result)
                    seen_records.add(dedup_key)
                    logger.info(f"✅ [DEDUP] Added unique record: date={dedup_key[0]}, time={dedup_key[1]}, provider={dedup_key[2]}")
                else:
                    if dedup_key in seen_records:
                        logger.warning(f"⚠️ [DEDUP] Skipped duplicate: {dedup_key}")
                    else:
                        logger.warning(f"⚠️ [DEDUP] Skipped incomplete record (missing key fields): {dedup_key}")

        # If we have results from correlation, return them
        if results:
            logger.info(f"🔗 [CORRELATION] Successfully correlated {len(results)} records")
            return results

        # PHASE 3: Fallback to old logic if correlation produced no results
        logger.info(f"🔗 [CORRELATION] No correlated results, falling back to direct parsing")

        for item in captured_data:
            api_url = item['api_url']
            data = item['data']

            logger.info(f"🌐 [API-PARSE] Processing response from: {api_url}")

            try:
                # Try different response structures
                # Structure 1: YClients JSON API format {data: [{type, id, attributes: {...}}]}
                if isinstance(data, dict) and 'data' in data:
                    items = data['data']
                    if isinstance(items, list):
                        logger.info(f"🔍 [API-PARSE] Found {len(items)} items in data array for {api_url}")
                        for idx, booking in enumerate(items):
                            # Check if this is JSON API format with attributes
                            if isinstance(booking, dict) and 'attributes' in booking:
                                # Extract the actual data from attributes
                                booking_data = booking['attributes']
                                # Also include type and id for context
                                booking_data['_type'] = booking.get('type')
                                booking_data['_id'] = booking.get('id')
                                logger.info(f"🔍 [API-PARSE] Item {idx+1}: type={booking.get('type')}, attributes keys={list(booking_data.keys())}")
                                result = self.parse_booking_from_api(booking_data, api_url)
                            else:
                                # Standard format
                                logger.info(f"🔍 [API-PARSE] Item {idx+1}: standard format, keys={list(booking.keys()) if isinstance(booking, dict) else 'not dict'}")
                                result = self.parse_booking_from_api(booking, api_url)
                            if result:
                                results.append(result)
                                logger.info(f"✅ [API-PARSE] Successfully added item {idx+1}")
                            else:
                                logger.warning(f"⚠️ [API-PARSE] Item {idx+1} returned None (filtered out)")

                # Structure 2: {result: {slots: [...]}}
                elif isinstance(data, dict) and 'result' in data:
                    result_data = data['result']
                    if isinstance(result_data, dict) and 'slots' in result_data:
                        for booking in result_data['slots']:
                            result = self.parse_booking_from_api(booking, api_url)
                            if result:
                                results.append(result)
                    elif isinstance(result_data, list):
                        for booking in result_data:
                            result = self.parse_booking_from_api(booking, api_url)
                            if result:
                                results.append(result)

                # Structure 3: [{time, price, available}] - direct array
                elif isinstance(data, list):
                    for booking in data:
                        result = self.parse_booking_from_api(booking, api_url)
                        if result:
                            results.append(result)

                # Structure 4: Direct object
                elif isinstance(data, dict):
                    result = self.parse_booking_from_api(data, api_url)
                    if result:
                        results.append(result)

            except Exception as e:
                logger.warning(f"🌐 [API-PARSE] Failed to parse response structure: {e}")

        logger.info(f"🌐 [API-PARSE] Extracted {len(results)} booking records from API")
        return results

    def parse_booking_from_api(self, booking_obj: Dict, api_url: str) -> Optional[Dict]:
        """
        Parse individual booking object from API response.
        Tries common field names used in booking APIs.

        Args:
            booking_obj: Dictionary containing booking data
            api_url: Source API URL for reference

        Returns:
            Parsed booking dict or None if insufficient data
        """
        try:
            # YClients предоставляет поле 'time' напрямую - ИСПОЛЬЗУЕМ ЕГО!
            # Ответ API: {'datetime': '2025-10-02T08:00:00+03:00', 'time': '8:00', 'is_bookable': True}

            # Получаем time напрямую из YClients (наиболее надежный способ)
            result_time = booking_obj.get('time')
            result_date = None

            # Получаем дату из поля datetime
            datetime_str = booking_obj.get('datetime', '')
            if datetime_str and 'T' in datetime_str:
                try:
                    result_date = datetime_str.split('T')[0]  # "2025-10-02"
                    # Если time не предоставлен напрямую, парсим из datetime
                    if not result_time:
                        time_part = datetime_str.split('T')[1] if len(datetime_str.split('T')) > 1 else ''
                        result_time = time_part.split('+')[0].split('-')[0][:5]  # "08:00"
                    logger.info(f"[PARSE-DEBUG] datetime={datetime_str} -> date={result_date}, time={result_time}")
                except Exception as e:
                    logger.error(f"[PARSE-DEBUG] Failed to parse datetime '{datetime_str}': {e}")

            # Резервные варианты для отсутствующих полей
            if not result_date:
                result_date = booking_obj.get('date') or booking_obj.get('booking_date')
            if not result_time:
                result_time = booking_obj.get('slot_time') or booking_obj.get('start_time')

            logger.info(f"[DIRECT-USE] Final values: date={result_date}, time={result_time}")

            result = {
                'url': api_url,
                'date': result_date,
                'time': result_time,
                'price': (booking_obj.get('price') or
                         booking_obj.get('cost') or
                         booking_obj.get('amount') or
                         booking_obj.get('price_min') or
                         booking_obj.get('price_max')),
                'provider': (booking_obj.get('provider') or
                            booking_obj.get('master') or
                            booking_obj.get('staff') or
                            booking_obj.get('staff_name') or
                            booking_obj.get('service_name')),
                'duration': booking_obj.get('duration', 60),
                'available': booking_obj.get('available') or booking_obj.get('is_bookable', True),
                'service_name': (booking_obj.get('service_name') or
                                booking_obj.get('service') or
                                booking_obj.get('title')),
                'booking_type': booking_obj.get('_type'),  # From JSON API format
                'extracted_at': datetime.now().isoformat()
            }

            # DEBUG: Log what we actually parsed
            logger.info(f"🔍 [DEBUG] Parsed result: date={result.get('date')}, time={result.get('time')}, datetime_str={datetime_str[:30] if datetime_str else 'None'}")

            # Only return if we have required fields (BOTH date AND time)
            if result['date'] and result['time']:
                logger.info(f"✅ [API-PARSE] Parsed booking: date={result['date']}, time={result['time']}, price={result['price']}, type={result.get('booking_type')}")
                return result
            else:
                logger.warning(f"⚠️ [API-PARSE] Skipping object without date/time: {str(booking_obj)[:150]}")

        except Exception as e:
            logger.warning(f"❌ [API-PARSE] Failed to parse booking object: {e} | Data: {str(booking_obj)[:150]}")

        return None

    async def detect_and_handle_page_type(self, page: Page, original_url: str, current_url: str) -> List[Dict]:
        """
        Smart detection of YClients page type and routing to appropriate handler.

        Handles:
        - City/branch selection pages (redirected multi-location venues)
        - Menu pages (/personal/menu)
        - Time selection pages (/personal/select-time - mid-flow)
        - Standard record-type flow
        """
        try:
            page_title = await page.title()
            logger.info(f"🔍 [DETECTION] Page title: {page_title}")

            # Check for city/branch selection redirect
            if '/select-city' in current_url or '/select-branch' in current_url:
                logger.warning(f"⚠️ [DETECTION] Redirected to city/branch selection page")
                return await self.handle_multi_location_redirect(page, original_url)

            # Check if on menu page
            elif '/personal/menu' in current_url:
                logger.info(f"✅ [DETECTION] Menu page detected")
                return await self.handle_menu_page(page, current_url)

            # Check if already at time selection (mid-flow URL)
            elif '/personal/select-time' in current_url:
                logger.info(f"✅ [DETECTION] Time selection page (mid-flow entry)")
                return await self.handle_time_selection_page(page, current_url)

            # Standard flow (record-type or similar)
            else:
                logger.info(f"✅ [DETECTION] Standard booking flow page")
                return await self.navigate_yclients_flow(page, original_url)

        except Exception as e:
            logger.error(f"❌ [DETECTION] Error in page type detection: {str(e)}")
            # Fallback to standard flow
            return await self.navigate_yclients_flow(page, original_url)

    async def handle_multi_location_redirect(self, page: Page, original_url: str) -> List[Dict]:
        """
        Handle pages that redirect to city/branch selection.
        Try to select first available location and continue.
        """
        logger.info("🏢 [MULTI-LOC] Attempting to handle multi-location redirect")

        try:
            # Wait for page to fully load
            await page.wait_for_timeout(3000)

            # CRITICAL FIX: Use div with hasText filter to find location cards
            # Based on Playwright exploration findings - branch selection uses nested divs
            try:
                # Look for location names in the page
                location_patterns = [
                    'Lunda Padel',
                    'Padel',
                    'филиал',  # Branch in Russian
                ]

                for pattern in location_patterns:
                    try:
                        # Find clickable divs containing location names
                        locations = await page.locator(f'div[cursor="pointer"]:has-text("{pattern}")').all()

                        # Alternative: Find any clickable generic elements with location text
                        if not locations:
                            locations = await page.locator(f'generic[cursor="pointer"]:has-text("{pattern}")').all()

                        # Fallback: Use JavaScript to find clickable elements with text content
                        if not locations:
                            locations = await page.evaluate(f'''() => {{
                                const pattern = "{pattern}";
                                const clickable = [];
                                const allDivs = document.querySelectorAll('div, generic');

                                allDivs.forEach(div => {{
                                    const style = window.getComputedStyle(div);
                                    const text = div.textContent || '';

                                    if (text.includes(pattern) &&
                                        style.cursor === 'pointer' &&
                                        div.offsetHeight > 0) {{
                                        clickable.push(div);
                                    }}
                                }});

                                return clickable;
                            }}''')

                            if locations and len(locations) > 0:
                                logger.info(f"🏢 [MULTI-LOC] Found {len(locations)} clickable locations via JS with pattern '{pattern}'")
                                # Click first one using JavaScript
                                await page.evaluate('(el) => el.click()', locations[0])
                                await page.wait_for_load_state('networkidle', timeout=10000)

                                new_url = page.url
                                logger.info(f"🏢 [MULTI-LOC] After JS click, new URL: {new_url}")
                                return await self.detect_and_handle_page_type(page, original_url, new_url)

                        if locations and len(locations) > 0:
                            logger.info(f"🏢 [MULTI-LOC] Found {len(locations)} clickable locations with pattern '{pattern}'")

                            # Click first available location
                            first_location = locations[0]
                            location_text = await first_location.text_content()
                            logger.info(f"🏢 [MULTI-LOC] Clicking first location: {location_text[:100]}")

                            await first_location.click(force=True, timeout=5000)
                            await page.wait_for_load_state('networkidle', timeout=10000)

                            new_url = page.url
                            logger.info(f"🏢 [MULTI-LOC] After click, new URL: {new_url}")
                            return await self.detect_and_handle_page_type(page, original_url, new_url)

                    except Exception as e:
                        logger.debug(f"🏢 [MULTI-LOC] Pattern '{pattern}' search failed: {e}")
                        continue

            except Exception as e:
                logger.warning(f"🏢 [MULTI-LOC] Advanced location search failed: {e}")

            # Fallback to old selectors
            branch_selectors = [
                'div[cursor="pointer"]',    # Generic clickable divs
                'ui-kit-simple-cell',       # YClients UI cells
                'a[href*="/company/"]',     # Links to specific company pages
                'a[href*="record-type"]',   # Direct booking links
            ]

            for selector in branch_selectors:
                try:
                    elements = await page.locator(selector).all()
                    if elements and len(elements) > 0:
                        logger.info(f"🏢 [MULTI-LOC] Found {len(elements)} elements with selector: {selector}")

                        # Click first location (use force for Angular components)
                        first_element = elements[0]
                        element_text = await first_element.text_content()
                        logger.info(f"🏢 [MULTI-LOC] Clicking first location: {element_text[:50]}")

                        await first_element.click(force=True, timeout=5000)
                        await page.wait_for_load_state('networkidle', timeout=10000)

                        # Now recursively detect the new page type
                        new_url = page.url
                        logger.info(f"🏢 [MULTI-LOC] After click, new URL: {new_url}")
                        return await self.detect_and_handle_page_type(page, original_url, new_url)

                except Exception as e:
                    logger.debug(f"🏢 [MULTI-LOC] Selector {selector} failed: {e}")
                    continue

            # If no location links found, cannot proceed
            logger.warning(f"⚠️ [MULTI-LOC] No location links found, cannot select branch")
            logger.info(f"🏢 [MULTI-LOC] Page HTML snippet: {(await page.content())[:500]}")
            return []

        except Exception as e:
            logger.error(f"❌ [MULTI-LOC] Error handling multi-location: {str(e)}")
            return []

    async def handle_menu_page(self, page: Page, url: str) -> List[Dict]:
        """
        Handle /personal/menu pages where services are listed but as menu items.
        Extract available services and navigate to each.
        """
        logger.info("📋 [MENU] Extracting services from menu page")

        results = []
        try:
            # Menu pages typically have service cards/cells
            # Try to find clickable service elements
            service_selectors = [
                'ui-kit-simple-cell',
                '[class*="service"]',
                'a[href*="select-time"]',
                '.menu-item',
            ]

            for selector in service_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    services = await page.locator(selector).all()

                    if services:
                        logger.info(f"📋 [MENU] Found {len(services)} services with selector: {selector}")

                        # Click on first few services to get their booking flows
                        for i, service in enumerate(services[:3]):  # Limit to 3 services
                            try:
                                service_text = await service.text_content()
                                logger.info(f"📋 [MENU] Clicking service {i+1}: {service_text[:30]}")

                                await service.click()
                                await page.wait_for_load_state('networkidle', timeout=5000)

                                # Now we should be in booking flow - detect and continue
                                current_url = page.url
                                service_results = await self.detect_and_handle_page_type(page, url, current_url)
                                results.extend(service_results)

                                # Go back to menu
                                await page.go_back()
                                await page.wait_for_load_state('networkidle', timeout=5000)

                            except Exception as e:
                                logger.warning(f"⚠️ [MENU] Failed to process service {i+1}: {e}")
                                continue

                        break  # Found services, stop trying other selectors

                except Exception as e:
                    logger.debug(f"📋 [MENU] Selector {selector} failed: {e}")
                    continue

            return results

        except Exception as e:
            logger.error(f"❌ [MENU] Error handling menu page: {str(e)}")
            return []

    async def handle_time_selection_page(self, page: Page, url: str) -> List[Dict]:
        """
        Handle pages that start directly at time selection (/personal/select-time).
        CRITICAL FIX: Now navigates full flow TIME → COURT → SERVICE to capture ALL data.

        Real YClients flow (confirmed from Playwright exploration):
        1. TIME selection (this page) - capture dates/times
        2. COURT selection - capture court names (DOM scrape)
        3. SERVICE selection - capture prices (DOM scrape)
        """
        logger.info("⏰ [TIME-PAGE] Starting FULL flow navigation (TIME → COURT → SERVICE)")

        results = []
        scraped_data = {'dates': [], 'times': [], 'courts': [], 'services': []}

        try:
            # Wait for time selection elements
            await page.wait_for_timeout(2000)  # Let page fully load

            # Check if page shows "No free time" message with "Go to nearest date" button
            try:
                nearest_date_btn = page.get_by_role('button', name=re.compile(r'Перейти.*ближайшей.*дате'))
                if await nearest_date_btn.is_visible(timeout=2000):
                    logger.info("⏰ [TIME-PAGE] Found 'Go to nearest date' button, clicking...")
                    await nearest_date_btn.click(force=True)
                    await page.wait_for_timeout(3000)  # Wait for time slots to appear

                    # Time slots should now be visible - proceed to click one
                    try:
                        # Look for time slots (format: "9:00", "22:00", etc.)
                        time_slots = await page.get_by_text(re.compile(r'^\d{1,2}:\d{2}$')).all()
                        if not time_slots:
                            raise Exception("No time slots found")
                        time_slot = time_slots[0]
                        time_text = await time_slot.text_content()
                        logger.info(f"⏰ [TIME-PAGE] Clicking time slot: {time_text}")

                        await time_slot.click(force=True)
                        await page.wait_for_timeout(1500)

                        # Click Продолжить button
                        continue_btn = page.get_by_role('button', name='Продолжить')
                        if await continue_btn.is_visible(timeout=2000):
                            logger.info("🎯 Clicking Продолжить")
                            await continue_btn.click(force=True)
                            await page.wait_for_load_state('networkidle', timeout=10000)

                            # Should now be on select-services page
                            if 'select-services' in page.url:
                                logger.info("✅ [FLOW-A] On service page - scraping prices")

                                # Get provider (court name) - try multiple page structures
                                provider = 'Unknown'
                                provider_selectors = [
                                    'paragraph',                     # Structure A (b861100 - Angular paragraph element)
                                    'p.label.category-title',       # Structure A alternative
                                    'div.header_title',             # Structure B (b1009933 - TK Raketion)
                                    'div.title-block__title',       # Structure C (alternative)
                                    'h1.category-title',            # Structure D (fallback)
                                    '.service-category-title',      # Structure E (fallback)
                                ]

                                for selector in provider_selectors:
                                    try:
                                        provider_el = page.locator(selector).first
                                        provider_text = await provider_el.text_content(timeout=2000)
                                        if provider_text and provider_text.strip():
                                            provider = provider_text.strip()
                                            logger.info(f"🏟️ Provider found with selector '{selector}': {provider}")
                                            break
                                    except Exception:
                                        continue

                                if provider == 'Unknown':
                                    logger.warning(f"⚠️ Failed to get provider: No matching selector found")

                                # Get prices (text with ₽ symbol)
                                try:
                                    price_elements = await page.get_by_text(re.compile(r'\d+[,\s]*\d*\s*₽')).all()
                                    logger.info(f"💰 Found {len(price_elements)} prices")

                                    # Get date (from button click - it's the suggested date)
                                    from datetime import timedelta
                                    suggested_date = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')

                                    for price_el in price_elements:
                                        price_text = await price_el.text_content()
                                        price_clean = price_text.strip()

                                        result = {
                                            'url': page.url,
                                            'date': suggested_date,
                                            'time': time_text.strip(),
                                            'provider': provider,
                                            'price': price_clean,
                                            'service_name': 'Court Rental',
                                            'duration': 60,
                                            'available': True,
                                            'extracted_at': datetime.now().isoformat()
                                        }
                                        results.append(result)
                                        logger.info(f"✅ [PRODUCTION-PROOF] PRICE CAPTURED: {price_clean}")
                                        logger.info(f"✅ [PRODUCTION-PROOF] Full record: date={suggested_date}, time={time_text.strip()}, provider={provider}, price={price_clean}")

                                    # Return early with results!
                                    if results:
                                        logger.info(f"✅ [TIME-PAGE] Extracted {len(results)} records from nearest date")
                                        return results

                                except Exception as e:
                                    logger.error(f"❌ Failed to scrape prices: {e}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to process nearest date: {e}")
            except:
                pass  # Button not found, continue with date selection

            # Check if time slots are already visible (after clicking nearest date button)
            try:
                # Wait a bit for DOM to update after clicking button
                await page.wait_for_timeout(1000)

                # Try to find time slots using pattern matching
                # Time slots contain text like "9:00", "10:30" etc.
                # Use partial match since elements may have whitespace
                time_slot_candidates = await page.get_by_text(re.compile(r'\d{1,2}:\d{2}')).all()

                # Filter to only actual time slots (not other elements with colons)
                time_slots = []
                for candidate in time_slot_candidates:
                    text = await candidate.text_content()
                    text_clean = text.strip() if text else ''
                    # Check if it matches time format (HH:MM)
                    if re.match(r'^\d{1,2}:\d{2}$', text_clean):
                        time_slots.append(candidate)

                if len(time_slots) > 0:
                    logger.info(f"⏰ [TIME-PAGE] Time slots already visible, found {len(time_slots)} slots")
                    logger.info("⏰ [TIME-PAGE] Extracting directly without clicking dates...")

                    # Get the current date (shown on page)
                    try:
                        # Try to find selected/highlighted date
                        selected_date_text = await page.locator('.calendar-day.selected, .calendar-day.active, [class*="selected"][class*="date"]').first.text_content()
                        parsed_date = self.parse_date(selected_date_text)
                    except:
                        parsed_date = datetime.now().strftime('%Y-%m-%d')

                    logger.info(f"⏰ [TIME-PAGE] Current date: {parsed_date}")

                    # Process each visible time slot
                    for slot_idx, slot in enumerate(time_slots[:3]):
                        try:
                            time_text = await slot.text_content()
                            time_clean = time_text.strip() if time_text else ''
                            logger.info(f"⏰ [STEP-2] Clicking time slot: {time_clean}")

                            await slot.click(force=True, timeout=5000)
                            await page.wait_for_timeout(1500)

                            # Check for "Продолжить" button
                            try:
                                continue_btn = page.get_by_role('button', name='Продолжить')
                                if await continue_btn.is_visible(timeout=2000):
                                    logger.info(f"🎯 [STEP-2] Clicking 'Продолжить' to next page")
                                    await continue_btn.click()
                                    await page.wait_for_load_state('networkidle', timeout=10000)

                                    current_url = page.url
                                    logger.info(f"🔍 [STEP-2] Landed on: {current_url}")

                                    # Check if we're on service page
                                    if 'select-services' in current_url:
                                        logger.info(f"✅ [FLOW-A] Direct service page - scraping prices")

                                        # Get provider/court name
                                        provider_name = 'Unknown'
                                        try:
                                            provider_el = await page.locator('paragraph').first
                                            provider_name = await provider_el.text_content()
                                            provider_name = provider_name.strip() if provider_name else 'Unknown'
                                            logger.info(f"🏟️ [FLOW-A] Provider: {provider_name}")
                                        except Exception as e:
                                            logger.warning(f"⚠️ [FLOW-A] Failed to get provider: {e}")

                                        # Get all prices
                                        try:
                                            price_elements = await page.get_by_text(re.compile(r'\d+[,\s]*\d*\s*₽')).all()
                                            logger.info(f"💰 [FLOW-A] Found {len(price_elements)} prices")

                                            for idx, price_el in enumerate(price_elements):
                                                try:
                                                    price_text = await price_el.text_content()
                                                    price_clean = price_text.strip() if price_text else None

                                                    if price_clean:
                                                        result = {
                                                            'url': page.url,
                                                            'date': parsed_date,
                                                            'time': time_clean,
                                                            'provider': provider_name,
                                                            'price': price_clean,
                                                            'service_name': 'Unknown Service',
                                                            'duration': 60,
                                                            'available': True,
                                                            'extracted_at': datetime.now().isoformat()
                                                        }
                                                        results.append(result)
                                                        logger.info(f"✅ [FLOW-A] Scraped: {parsed_date} {time_clean} → {provider_name} → {price_clean}")
                                                except Exception as e:
                                                    logger.warning(f"⚠️ [FLOW-A] Failed to extract price {idx+1}: {e}")

                                        except Exception as e:
                                            logger.error(f"❌ [FLOW-A] Failed to get prices: {e}")

                                        # Go back to time selection
                                        await page.go_back()
                                        await page.wait_for_timeout(1000)

                            except Exception as e:
                                logger.warning(f"⚠️ [STEP-2] No 'Продолжить' button: {e}")

                        except Exception as e:
                            logger.warning(f"⚠️ [STEP-2] Failed to process time slot {slot_idx+1}: {e}")
                            continue

                    # If we got results, return them
                    if results:
                        logger.info(f"✅ [TIME-PAGE] Extracted {len(results)} records from visible time slots")
                        return results

            except:
                pass  # Time slots not visible, continue with date iteration

            # STEP 1: Extract dates from DOM
            date_selectors = [
                '.calendar-day:not(.disabled)',
                '[class*="date"]',
                '[data-date]',
            ]

            dates_found = []
            for selector in date_selectors:
                try:
                    dates = await page.locator(selector).all()
                    if dates and len(dates) > 0:
                        dates_found = dates
                        logger.info(f"⏰ [TIME-PAGE] Found {len(dates)} dates with selector: {selector}")
                        break
                except:
                    continue

            if not dates_found:
                logger.warning("⚠️ [TIME-PAGE] No dates found on time selection page")
                return []

            # STEP 2: Navigate through dates → times → courts → services
            for date_idx, date in enumerate(dates_found[:2]):  # Limit to 2 dates for performance
                try:
                    date_text = await date.text_content()
                    parsed_date = self.parse_date(date_text)
                    logger.info(f"⏰ [STEP-1] Processing date {date_idx+1}: {date_text[:20]} → {parsed_date}")

                    # Scroll into view and click date to load time slots
                    await date.scroll_into_view_if_needed()
                    await page.wait_for_timeout(500)
                    await date.click(force=True, timeout=5000)
                    await page.wait_for_timeout(2000)  # Give time for slots to load

                    # Extract time slots for this date
                    time_slots = []
                    time_slot_selectors = [
                        '[data-time]',
                        'button[class*="time"]',
                        '.time-slot',
                        'div[class*="slot"]',
                    ]

                    for selector in time_slot_selectors:
                        try:
                            slots = await page.locator(selector).all()
                            if slots:
                                time_slots = slots
                                logger.info(f"⏰ [STEP-1] Found {len(time_slots)} time slots with selector: {selector}")
                                break
                        except:
                            continue

                    # Fallback: search for time patterns
                    if not time_slots:
                        time_slots = await page.get_by_text(re.compile(r'\d{1,2}:\d{2}')).all()
                        if time_slots:
                            logger.info(f"⏰ [STEP-1] Found {len(time_slots)} time slots via text pattern")

                    # Navigate through each time slot
                    for slot_idx, slot in enumerate(time_slots[:3]):  # Limit to 3 slots per date
                        try:
                            time_text = await slot.text_content()
                            time_clean = time_text.strip() if time_text else ''
                            logger.info(f"⏰ [STEP-2] Clicking time slot: {time_clean}")

                            # Click time slot
                            await slot.click(force=True, timeout=5000)
                            await page.wait_for_timeout(1500)

                            # Check for "Продолжить" button to go to next step
                            try:
                                continue_btn = page.get_by_role('button', name='Продолжить')
                                if await continue_btn.is_visible(timeout=2000):
                                    logger.info(f"🎯 [STEP-2] Clicking 'Продолжить' to next page")
                                    await continue_btn.click()
                                    await page.wait_for_load_state('networkidle', timeout=10000)

                                    # CHECK: Which page did we land on?
                                    current_url = page.url
                                    logger.info(f"🔍 [STEP-2] Landed on: {current_url}")

                                    # FLOW A: Direct to SERVICE page (no court selection!)
                                    if 'select-services' in current_url:
                                        logger.info(f"✅ [FLOW-A] Direct service page detected - scraping prices")

                                        # Get provider/court name from first paragraph
                                        provider_name = 'Unknown'
                                        try:
                                            provider_el = await page.locator('paragraph').first
                                            provider_name = await provider_el.text_content()
                                            provider_name = provider_name.strip() if provider_name else 'Unknown'
                                            logger.info(f"🏟️ [FLOW-A] Provider: {provider_name}")
                                        except Exception as e:
                                            logger.warning(f"⚠️ [FLOW-A] Failed to get provider: {e}")

                                        # Get all prices from page (they contain ₽ symbol)
                                        try:
                                            price_elements = await page.get_by_text(re.compile(r'\d+[,\s]*\d*\s*₽')).all()
                                            logger.info(f"💰 [FLOW-A] Found {len(price_elements)} prices")

                                            for idx, price_el in enumerate(price_elements):
                                                try:
                                                    price_text = await price_el.text_content()
                                                    price_clean = price_text.strip() if price_text else None

                                                    if price_clean:
                                                        # Try to get service name (text before price)
                                                        service_name = 'Unknown Service'
                                                        try:
                                                            # Get parent element and extract service text
                                                            parent = await price_el.locator('xpath=ancestor::*[contains(text(), "аренда")]').first
                                                            service_text = await parent.text_content()
                                                            if service_text and 'аренда' in service_text:
                                                                service_name = service_text.split('\n')[0].strip()
                                                        except:
                                                            pass

                                                        result = {
                                                            'url': page.url,
                                                            'date': parsed_date,
                                                            'time': time_clean,
                                                            'provider': provider_name,
                                                            'price': price_clean,
                                                            'service_name': service_name,
                                                            'duration': 60,
                                                            'available': True,
                                                            'extracted_at': datetime.now().isoformat()
                                                        }
                                                        results.append(result)
                                                        logger.info(f"✅ [FLOW-A] Scraped: {parsed_date} {time_clean} → {provider_name} → {price_clean}")
                                                except Exception as e:
                                                    logger.warning(f"⚠️ [FLOW-A] Failed to extract price {idx+1}: {e}")

                                        except Exception as e:
                                            logger.error(f"❌ [FLOW-A] Failed to get prices: {e}")

                                        # Go back to time selection
                                        await page.go_back()
                                        await page.wait_for_timeout(1000)
                                        continue  # Skip court navigation logic

                                    # FLOW B: Court selection page (original multi-step flow)
                                    # STEP 3: Now on court selection page - SCRAPE COURT NAMES
                                    logger.info(f"🏟️ [STEP-3] On court selection page, scraping court names")

                                    court_selectors = [
                                        'ui-kit-simple-cell',
                                        '[class*="court"]',
                                        '[class*="staff"]',
                                        '.service-item',
                                    ]

                                    courts_found = []
                                    for selector in court_selectors:
                                        try:
                                            courts = await page.locator(selector).all()
                                            if courts and len(courts) > 0:
                                                courts_found = courts
                                                logger.info(f"🏟️ [STEP-3] Found {len(courts)} courts with selector: {selector}")
                                                break
                                        except:
                                            continue

                                    if not courts_found:
                                        logger.warning(f"⚠️ [STEP-3] No courts found on page")
                                        # Go back and continue with next time slot
                                        await page.go_back()
                                        await page.wait_for_timeout(1000)
                                        continue

                                    # Navigate through courts
                                    for court_idx, court in enumerate(courts_found[:3]):  # Limit to 3 courts
                                        try:
                                            # Extract court name BEFORE clicking
                                            court_name = 'Unknown'
                                            try:
                                                court_name_el = await court.locator('ui-kit-headline').first
                                                court_name = await court_name_el.text_content()
                                                court_name = court_name.strip() if court_name else 'Unknown'
                                            except:
                                                court_name = await court.text_content()
                                                court_name = court_name[:50].strip() if court_name else 'Unknown'

                                            logger.info(f"🏟️ [STEP-4] Clicking court: {court_name}")

                                            # Click court
                                            await court.click(force=True, timeout=5000)
                                            await page.wait_for_timeout(1500)

                                            # Click "Продолжить" to go to service/price page
                                            continue_btn2 = page.get_by_role('button', name='Продолжить')
                                            if await continue_btn2.is_visible(timeout=2000):
                                                logger.info(f"🎯 [STEP-4] Clicking 'Продолжить' to service/price page")
                                                await continue_btn2.click()
                                                await page.wait_for_load_state('networkidle', timeout=10000)

                                                # STEP 4: Now on service/price page - SCRAPE PRICES
                                                logger.info(f"💰 [STEP-5] On service/price page, scraping prices")

                                                # Extract service items with prices
                                                service_selectors = [
                                                    'ui-kit-simple-cell',
                                                    '[class*="service"]',
                                                    '.price-item',
                                                ]

                                                services_found = []
                                                for selector in service_selectors:
                                                    try:
                                                        services = await page.locator(selector).all()
                                                        if services and len(services) > 0:
                                                            services_found = services
                                                            logger.info(f"💰 [STEP-5] Found {len(services)} services with selector: {selector}")
                                                            break
                                                    except:
                                                        continue

                                                for svc_idx, service in enumerate(services_found):
                                                    try:
                                                        # Extract service name
                                                        service_name = 'Unknown Service'
                                                        try:
                                                            name_el = await service.locator('ui-kit-headline').first
                                                            service_name = await name_el.text_content()
                                                            service_name = service_name.strip() if service_name else 'Unknown Service'
                                                        except:
                                                            pass

                                                        # Extract price
                                                        price = 'Не найдена'
                                                        try:
                                                            price_el = await service.locator('ui-kit-title').first
                                                            price = await price_el.text_content()
                                                            price = self.clean_price(price) if price else 'Не найдена'
                                                        except:
                                                            pass

                                                        # Extract duration
                                                        duration = 60
                                                        try:
                                                            duration_el = await service.locator('ui-kit-body').first
                                                            duration_text = await duration_el.text_content()
                                                            duration = self.parse_duration(duration_text) if duration_text else 60
                                                        except:
                                                            pass

                                                        # Create complete booking record with ALL data
                                                        result = {
                                                            'url': page.url,
                                                            'date': parsed_date,
                                                            'time': time_clean,
                                                            'provider': court_name,
                                                            'price': price,
                                                            'service_name': service_name,
                                                            'duration': duration,
                                                            'available': True,
                                                            'extracted_at': datetime.now().isoformat()
                                                        }
                                                        results.append(result)
                                                        logger.info(f"✅ [STEP-5] Scraped complete record: date={parsed_date}, time={time_clean}, court={court_name}, price={price}")

                                                    except Exception as e:
                                                        logger.warning(f"⚠️ [STEP-5] Failed to extract service {svc_idx+1}: {e}")

                                                # Go back to court selection
                                                await page.go_back()
                                                await page.wait_for_timeout(1000)

                                        except Exception as e:
                                            logger.warning(f"⚠️ [STEP-4] Failed to process court {court_idx+1}: {e}")
                                            continue

                                    # Go back to time selection
                                    await page.go_back()
                                    await page.wait_for_timeout(1000)

                            except Exception as e:
                                logger.warning(f"⚠️ [STEP-2] No 'Продолжить' button or navigation failed: {e}")

                        except Exception as e:
                            logger.warning(f"⚠️ [STEP-2] Failed to process time slot {slot_idx+1}: {e}")
                            continue

                except Exception as e:
                    logger.warning(f"⚠️ [STEP-1] Failed to process date {date_idx+1}: {e}")
                    continue

            logger.info(f"✅ [TIME-PAGE] Complete flow navigation finished: {len(results)} records extracted")
            return results

        except Exception as e:
            logger.error(f"❌ [TIME-PAGE] Error handling time selection page: {str(e)}")
            return []

    async def navigate_yclients_flow(self, page: Page, url: str) -> List[Dict]:
        """
        Navigate through YClients 4-step booking flow.
        Step 1: Service selection (record-type)
        Step 2: Court selection (select-master)
        Step 3: Date/time selection (select-time)
        Step 4: Service packages with prices (select-services)
        """
        results = []
        logger.info(f"🔍 [DEBUG] Starting 4-step YClients navigation for {url}")

        try:
            # Step 1: Load and select service type
            logger.info(f"🔍 [DEBUG] Step 1: Loading page and waiting for ui-kit-simple-cell")
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_selector('ui-kit-simple-cell', timeout=10000)
            logger.info(f"🔍 [DEBUG] Step 1: Page loaded, title: {await page.title()}")
            
            # Click on "Индивидуальные услуги" or first available service
            service_links = await page.get_by_role('link').all()
            logger.info(f"🔍 [DEBUG] Step 1: Found {len(service_links)} service links")
            service_clicked = False
            for link in service_links:
                text = await link.text_content()
                if 'Индивидуальные' in text or 'услуги' in text.lower():
                    logger.info(f"🔍 [DEBUG] Step 1: Clicking service link: {text[:50]}")
                    await link.click()
                    service_clicked = True
                    break

            if not service_clicked:
                logger.warning(f"⚠️ [DEBUG] Step 1: No matching service link found, trying first link")
                if service_links:
                    await service_links[0].click()

            # Step 2: Select courts
            logger.info(f"🔍 [DEBUG] Step 2: Waiting for select-master page")
            await page.wait_for_url('**/personal/select-master**')
            await page.wait_for_selector('ui-kit-simple-cell')
            logger.info(f"🔍 [DEBUG] Step 2: On select-master page")

            courts = await page.locator('ui-kit-simple-cell').all()
            logger.info(f"🔍 [DEBUG] Step 2: Found {len(courts)} courts")
            for i, court in enumerate(courts[:3]):  # Limit to first 3 courts for testing
                court_name = await court.locator('ui-kit-headline').text_content()
                logger.info(f"🔍 [DEBUG] Step 2: Processing court {i+1}/3: {court_name[:50]}")
                await court.click()

                # Continue to date selection
                continue_btn = page.get_by_role('button', { 'name': 'Продолжить' })
                if await continue_btn.is_visible():
                    logger.info(f"🔍 [DEBUG] Step 2: Clicking 'Продолжить' button")
                    await continue_btn.click()

                # Step 3: Select dates and times
                logger.info(f"🔍 [DEBUG] Step 3: Waiting for select-time page")
                await page.wait_for_url('**/personal/select-time**')
                logger.info(f"🔍 [DEBUG] Step 3: Extracting time slots for {court_name[:30]}")
                before_count = len(results)
                await self.extract_time_slots_with_prices(page, court_name, results)
                after_count = len(results)
                logger.info(f"🔍 [DEBUG] Step 3: Extracted {after_count - before_count} slots for this court")

                # Go back to court selection
                await page.go_back()
                await page.wait_for_selector('ui-kit-simple-cell')

        except Exception as e:
            logger.error(f"❌ [DEBUG] Error in 4-step navigation: {str(e)}")
            logger.error(f"❌ [DEBUG] Current URL: {page.url}")
            logger.error(f"❌ [DEBUG] Page title: {await page.title()}")

        logger.info(f"🔍 [DEBUG] Navigation complete: extracted {len(results)} total results")
        if not results:
            logger.warning(f"⚠️ [DEBUG] ZERO results extracted! This needs investigation.")

        return results

    async def extract_time_slots_with_prices(self, page: Page, court_name: str, results: List[Dict]):
        """Extract time slots and navigate to get prices."""
        logger.info(f"🔍 [DEBUG] extract_time_slots_with_prices: Starting for court {court_name[:30]}")

        try:
            # Get available dates
            dates = await page.locator('.calendar-day:not(.disabled)').all()
            logger.info(f"🔍 [DEBUG] Found {len(dates)} available dates")

            for date_idx, date in enumerate(dates[:2]):  # Limit to 2 dates for testing
                date_text = await date.text_content()
                logger.info(f"🔍 [DEBUG] Processing date {date_idx+1}/2: {date_text[:20]}")
                await date.click()
                await page.wait_for_timeout(1000)

                # Get time slots
                time_slots = await page.locator('[data-time]').all()
                if not time_slots:
                    # Try alternative selector
                    logger.warning(f"⚠️ [DEBUG] No [data-time] slots found, trying text regex")
                    time_slots = await page.get_by_text(re.compile(r'\d{1,2}:\d{2}')).all()

                logger.info(f"🔍 [DEBUG] Found {len(time_slots)} time slots for this date")

                for slot_idx, slot in enumerate(time_slots[:3]):  # Limit to 3 slots per date
                    time_text = await slot.text_content()
                    logger.info(f"🔍 [DEBUG] Processing time slot {slot_idx+1}/3: {time_text[:10]}")
                    await slot.click()

                    # Continue to services/prices
                    continue_btn = page.get_by_role('button', { 'name': 'Продолжить' })
                    if await continue_btn.is_visible():
                        await continue_btn.click()

                        # Step 4: Extract prices from service packages
                        logger.info(f"🔍 [DEBUG] Step 4: Waiting for select-services page")
                        await page.wait_for_url('**/personal/select-services**')
                        await page.wait_for_selector('ui-kit-simple-cell')
                        logger.info(f"🔍 [DEBUG] Step 4: On select-services page")

                        services = await page.locator('ui-kit-simple-cell').all()
                        logger.info(f"🔍 [DEBUG] Step 4: Found {len(services)} services")
                        for svc_idx, service in enumerate(services):
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
                                logger.info(f"🔍 [DEBUG] Step 4: Extracted service {svc_idx+1}: {name[:30]} - {price}")
                            except Exception as e:
                                logger.warning(f"⚠️ [DEBUG] Failed to extract service {svc_idx+1}: {e}")

                        # Go back to time selection
                        await page.go_back()
                        await page.wait_for_timeout(1000)
        except Exception as e:
            logger.error(f"❌ [DEBUG] Error extracting time slots with prices: {str(e)}")
            logger.error(f"❌ [DEBUG] Current URL when error occurred: {page.url}")

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
                logger.info("🎯 YClients URL detected, checking page type...")

                # SMART DETECTION: Check what page we actually landed on after navigation
                await self.page.wait_for_load_state('networkidle', timeout=5000)
                current_url = self.page.url
                logger.info(f"🔍 [DETECTION] Current URL after load: {current_url}")

                # Try API interception first (best for SPAs), fallback to DOM scraping
                try:
                    logger.info("🌐 [STRATEGY] Attempting API-based extraction first...")
                    all_data = await self.extract_via_api_interception(self.page, url)

                    # If API mode got data, use it
                    if all_data and len(all_data) > 0:
                        logger.info(f"✅ [STRATEGY] API mode succeeded: {len(all_data)} records")
                    else:
                        # Fallback to DOM scraping
                        logger.info("⚠️ [STRATEGY] API mode returned 0 records, falling back to DOM scraping")
                        all_data = await self.detect_and_handle_page_type(self.page, url, current_url)
                except Exception as e:
                    logger.error(f"❌ [STRATEGY] API mode failed: {e}, falling back to DOM scraping")
                    all_data = await self.detect_and_handle_page_type(self.page, url, current_url)
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
