"""
YCLIENTS Parser - Основной модуль парсинга данных с платформы YCLIENTS.
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
from src.parser.data_extractor import DataExtractor
from src.parser.enhanced_data_extractor import EnhancedDataExtractor
from src.parser.improved_data_extractor import ImprovedDataExtractor
from src.parser.selectors import SELECTORS
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
        # Используем улучшенный экстрактор данных
        self.data_extractor = ImprovedDataExtractor()
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
            captcha_exists = await self.page.query_selector(SELECTORS["captcha"])
            if captcha_exists:
                logger.warning("Обнаружена CAPTCHA, попытка обхода...")
                # Здесь могла бы быть реализация обхода капчи
                # В данной реализации просто закрываем страницу и меняем прокси
                return False
            
            # Проверка на блокировку IP
            blocked_ip = await self.page.query_selector(SELECTORS["ip_blocked"])
            if blocked_ip:
                logger.warning("IP заблокирован, смена прокси")
                return False
                
            # Другие проверки на антибот-защиту...
            
            return True
        except Exception as e:
            logger.error(f"Ошибка при проверке антибот-защиты: {str(e)}")
            return False

    async def extract_available_dates(self) -> List[Dict[str, Any]]:
        """
        Извлечение доступных дат бронирования.
        
        Returns:
            List[Dict[str, Any]]: Список доступных дат
        """
        logger.info("Извлечение доступных дат бронирования")
        try:
            # Ожидаем загрузки календаря
            await self.page.wait_for_selector(SELECTORS["calendar"], timeout=TIMEOUT)
            
            # Получаем элементы доступных дат
            date_elements = await self.page.query_selector_all(SELECTORS["available_dates"])
            
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
            date_selector = SELECTORS["date_selector"].format(date=date)
            date_element = await self.page.query_selector(date_selector)
            
            if not date_element:
                logger.warning(f"Элемент даты {date} не найден")
                return []
                
            # Кликаем на дату для загрузки доступных слотов
            await date_element.click()
            await asyncio.sleep(2)  # Ожидание загрузки слотов
            
            # Ждем появления контейнера со слотами
            await self.page.wait_for_selector(SELECTORS["time_slots_container"], timeout=TIMEOUT)
            
            # Получаем элементы доступных временных слотов
            slot_elements = await self.page.query_selector_all(SELECTORS["time_slots"])
            
            time_slots = []
            for slot_element in slot_elements:
                # Определяем, является ли дата выходным днем
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                is_weekend = date_obj.weekday() >= 5  # 5 и 6 - суббота и воскресенье
                
                # Используем улучшенный экстрактор данных для получения всех полей
                slot_data = await self.data_extractor.extract_booking_data_from_slot_improved(
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
                
            # Извлечение доступных дат
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
            
            return True, all_data
        
        except Exception as e:
            logger.error(f"Ошибка при парсинге прямой ссылки {url}: {str(e)}")
            return False, []
            # Навигация на страницу
            navigation_success = await self.navigate_to_url(url)
            if not navigation_success:
                logger.error(f"Не удалось загрузить страницу: {url}")
                return False, []
                
            # Проверка на антибот-защиту
            if not await self.check_for_antibot():
                logger.warning("Обнаружена защита от ботов, смена прокси и перезапуск")
                return False, []
                
            # Извлечение доступных дат
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
            
            success = True
            self.last_parsed_urls[url] = datetime.now()
            logger.info(f"Парсинг URL: {url} завершен успешно, получено {len(all_data)} записей")
        
        except Exception as e:
            logger.error(f"Ошибка при парсинге URL {url}: {str(e)}")
            success = False
        
        return success, all_data

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
