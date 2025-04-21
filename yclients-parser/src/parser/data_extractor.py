"""
Data Extractor - Извлечение и структурирование данных из HTML-элементов страницы YCLIENTS.

Модуль предоставляет методы для извлечения и обработки данных о бронировании
из HTML-элементов страницы YCLIENTS.
"""
import logging
import re
from datetime import datetime, time, date
from typing import Dict, List, Optional, Any, Tuple, Union

from playwright.async_api import ElementHandle, Page

from src.parser.selectors import SELECTORS, XPATH_SELECTORS


logger = logging.getLogger(__name__)


class DataExtractor:
    """
    Класс для извлечения и обработки данных из HTML-элементов.
    """

    def __init__(self):
        """Инициализация экстрактора данных."""
        # Регулярные выражения для извлечения данных
        self.time_pattern = re.compile(r'(\d{1,2})[:\.](\d{2})(?:\s*(AM|PM|am|pm))?')
        self.price_pattern = re.compile(r'(\d+[\.,]?\d*)')
        self.date_pattern = re.compile(r'(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{2,4})|(\d{4})[\/\.-](\d{1,2})[\/\.-](\d{1,2})')
        self.seat_pattern = re.compile(r'(?:место|корт|зал|комната|room|court|seat)\s*(?:[№#]?)?\s*(\d+)', re.IGNORECASE)

    async def extract_text_content(self, element: ElementHandle) -> str:
        """
        Извлечение текстового содержимого элемента.

        Args:
            element: HTML-элемент

        Returns:
            str: Текстовое содержимое элемента
        """
        try:
            text = await element.text_content()
            return text.strip() if text else ""
        except Exception as e:
            logger.error(f"Ошибка при извлечении текстового содержимого: {str(e)}")
            return ""

    async def extract_attribute(self, element: ElementHandle, attr: str) -> str:
        """
        Извлечение значения атрибута элемента.

        Args:
            element: HTML-элемент
            attr: Имя атрибута

        Returns:
            str: Значение атрибута
        """
        try:
            value = await element.get_attribute(attr)
            return value.strip() if value else ""
        except Exception as e:
            logger.error(f"Ошибка при извлечении атрибута {attr}: {str(e)}")
            return ""

    async def extract_date_from_element(self, element: ElementHandle) -> Optional[str]:
        """
        Извлечение даты из HTML-элемента.

        Args:
            element: HTML-элемент с датой

        Returns:
            Optional[str]: Строка с датой в формате YYYY-MM-DD или None
        """
        try:
            # Сначала пробуем получить дату из атрибутов
            date_attrs = ['data-date', 'date', 'value']
            for attr in date_attrs:
                date_str = await self.extract_attribute(element, attr)
                if date_str:
                    # Пробуем распарсить дату из атрибута
                    parsed_date = self.parse_date(date_str)
                    if parsed_date:
                        return parsed_date.isoformat()

            # Если не получилось из атрибутов, пробуем из текста
            text = await self.extract_text_content(element)
            if text:
                parsed_date = self.parse_date(text)
                if parsed_date:
                    return parsed_date.isoformat()

            return None

        except Exception as e:
            logger.error(f"Ошибка при извлечении даты из элемента: {str(e)}")
            return None

    async def extract_time_from_element(self, element: ElementHandle) -> Optional[str]:
        """
        Извлечение времени из HTML-элемента.

        Args:
            element: HTML-элемент с временем

        Returns:
            Optional[str]: Строка с временем в формате HH:MM:SS или None
        """
        try:
            # Сначала пробуем получить время из атрибутов
            time_attrs = ['data-time', 'time', 'value']
            for attr in time_attrs:
                time_str = await self.extract_attribute(element, attr)
                if time_str:
                    # Пробуем распарсить время из атрибута
                    parsed_time = self.parse_time(time_str)
                    if parsed_time:
                        return parsed_time.isoformat()

            # Если не получилось из атрибутов, пробуем из текста
            text = await self.extract_text_content(element)
            if text:
                parsed_time = self.parse_time(text)
                if parsed_time:
                    return parsed_time.isoformat()

            return None

        except Exception as e:
            logger.error(f"Ошибка при извлечении времени из элемента: {str(e)}")
            return None

    async def extract_price_from_element(self, element: ElementHandle) -> Optional[str]:
        """
        Извлечение цены из HTML-элемента.

        Args:
            element: HTML-элемент с ценой

        Returns:
            Optional[str]: Строка с ценой или None
        """
        try:
            # Сначала пробуем получить цену из атрибутов
            price_attrs = ['data-price', 'price', 'value']
            for attr in price_attrs:
                price_str = await self.extract_attribute(element, attr)
                if price_str:
                    return self.clean_price(price_str)

            # Если не получилось из атрибутов, пробуем из текста
            text = await self.extract_text_content(element)
            if text:
                return self.clean_price(text)

            # Если цена есть в дочернем элементе
            price_element = await element.query_selector(SELECTORS['slot_price'])
            if price_element:
                price_text = await self.extract_text_content(price_element)
                return self.clean_price(price_text)

            return None

        except Exception as e:
            logger.error(f"Ошибка при извлечении цены из элемента: {str(e)}")
            return None

    async def extract_provider_from_element(self, element: ElementHandle) -> Optional[str]:
        """
        Извлечение информации о провайдере из HTML-элемента.

        Args:
            element: HTML-элемент с информацией о провайдере

        Returns:
            Optional[str]: Строка с именем провайдера или None
        """
        try:
            # Сначала пробуем получить провайдера из атрибутов
            provider_attrs = ['data-provider', 'data-staff', 'provider', 'staff']
            for attr in provider_attrs:
                provider_str = await self.extract_attribute(element, attr)
                if provider_str:
                    return provider_str.strip()

            # Если не получилось из атрибутов, пробуем из дочернего элемента
            provider_element = await element.query_selector(SELECTORS['slot_provider'])
            if provider_element:
                provider_text = await self.extract_text_content(provider_element)
                return provider_text.strip()

            # Если провайдер есть в тексте элемента (редко), извлекаем его
            text = await self.extract_text_content(element)
            if text and ":" in text:
                # Предполагаем, что провайдер указан в формате "Имя: время"
                provider_part = text.split(":", 1)[0].strip()
                if provider_part and len(provider_part) < 50:  # Разумное ограничение
                    return provider_part

            return None

        except Exception as e:
            logger.error(f"Ошибка при извлечении провайдера из элемента: {str(e)}")
            return None

    async def extract_seat_from_element(self, element: ElementHandle) -> Optional[str]:
        """
        Извлечение номера места из HTML-элемента.

        Args:
            element: HTML-элемент с информацией о месте

        Returns:
            Optional[str]: Строка с номером места или None
        """
        try:
            # Сначала пробуем получить номер места из атрибутов
            seat_attrs = ['data-seat', 'data-court', 'data-room', 'seat', 'court', 'room']
            for attr in seat_attrs:
                seat_str = await self.extract_attribute(element, attr)
                if seat_str:
                    return seat_str.strip()

            # Если не получилось из атрибутов, пробуем из дочернего элемента
            seat_element = await element.query_selector(SELECTORS['slot_seat'])
            if seat_element:
                seat_text = await self.extract_text_content(seat_element)
                return self.extract_seat_number(seat_text)

            # Если номер места есть в тексте элемента, извлекаем его
            text = await self.extract_text_content(element)
            if text:
                seat_number = self.extract_seat_number(text)
                if seat_number:
                    return seat_number

            return None

        except Exception as e:
            logger.error(f"Ошибка при извлечении номера места из элемента: {str(e)}")
            return None

    async def extract_booking_data_from_slot(self, slot_element: ElementHandle) -> Dict[str, Any]:
        """
        Извлечение всех данных бронирования из элемента слота.

        Args:
            slot_element: HTML-элемент слота времени

        Returns:
            Dict[str, Any]: Словарь с данными бронирования
        """
        try:
            result = {}

            # Извлекаем время
            time_str = await self.extract_time_from_element(slot_element)
            if time_str:
                result['time'] = time_str

            # Извлекаем цену
            price = await self.extract_price_from_element(slot_element)
            if price:
                result['price'] = price

            # Извлекаем провайдера
            provider = await self.extract_provider_from_element(slot_element)
            if provider:
                result['provider'] = provider

            # Извлекаем номер места
            seat = await self.extract_seat_from_element(slot_element)
            if seat:
                result['seat_number'] = seat
            else:
                result['seat_number'] = "Не указано"

            # Дополнительные данные
            result['extracted_at'] = datetime.now().isoformat()

            return result

        except Exception as e:
            logger.error(f"Ошибка при извлечении данных из слота: {str(e)}")
            return {}

    async def extract_all_dates_from_page(self, page: Page) -> List[Dict[str, str]]:
        """
        Извлечение всех доступных дат с текущей страницы.

        Args:
            page: Страница браузера

        Returns:
            List[Dict[str, str]]: Список словарей с информацией о датах
        """
        try:
            logger.info("Извлечение всех доступных дат с текущей страницы")

            # Ждем загрузки календаря
            await page.wait_for_selector(SELECTORS['calendar'], timeout=5000)

            # Получаем элементы доступных дат
            date_elements = await page.query_selector_all(SELECTORS['available_dates'])
            logger.info(f"Найдено {len(date_elements)} элементов дат")

            result = []
            for date_element in date_elements:
                date_data = {}

                # Извлекаем дату из атрибута
                date_str = await self.extract_date_from_element(date_element)
                if date_str:
                    date_data['date'] = date_str
                else:
                    continue  # Пропускаем элементы без даты

                # Извлекаем отображаемый текст
                display_text = await self.extract_text_content(date_element)
                if display_text:
                    date_data['display_text'] = display_text

                # Атрибуты элемента
                # Получаем все атрибуты, которые могут быть полезны
                for attr in ['data-date', 'data-available', 'data-price', 'data-staff']:
                    attr_value = await self.extract_attribute(date_element, attr)
                    if attr_value:
                        date_data[attr] = attr_value

                result.append(date_data)

            return result

        except Exception as e:
            logger.error(f"Ошибка при извлечении всех дат: {str(e)}")
            return []

    async def extract_time_slots_for_date(self, page: Page, date_str: str) -> List[Dict[str, Any]]:
        """
        Извлечение всех временных слотов для выбранной даты.

        Args:
            page: Страница браузера
            date_str: Строка с датой

        Returns:
            List[Dict[str, Any]]: Список словарей с информацией о временных слотах
        """
        try:
            logger.info(f"Извлечение временных слотов для даты {date_str}")

            # Найти и выбрать элемент даты
            date_selector = SELECTORS['date_selector'].format(date=date_str)
            date_element = await page.query_selector(date_selector)

            if not date_element:
                logger.warning(f"Элемент даты {date_str} не найден")
                return []

            # Кликаем на дату для загрузки доступных слотов
            await date_element.click()

            # Ждем появления контейнера со слотами
            try:
                await page.wait_for_selector(SELECTORS['time_slots_container'], timeout=5000)
            except Exception as e:
                logger.warning(f"Не удалось дождаться контейнера временных слотов: {str(e)}")
                # Проверяем наличие временных слотов без контейнера
                slot_elements = await page.query_selector_all(SELECTORS['time_slots'])
                if not slot_elements:
                    return []

            # Получаем элементы доступных временных слотов
            slot_elements = await page.query_selector_all(SELECTORS['time_slots'])
            logger.info(f"Найдено {len(slot_elements)} элементов временных слотов")

            result = []
            for slot_element in slot_elements:
                # Извлекаем все данные из слота
                slot_data = await self.extract_booking_data_from_slot(slot_element)

                # Добавляем дату
                slot_data['date'] = date_str

                result.append(slot_data)

            return result

        except Exception as e:
            logger.error(f"Ошибка при извлечении временных слотов для даты {date_str}: {str(e)}")
            return []

    def parse_date(self, date_str: str) -> Optional[date]:
        """
        Парсинг строки даты в объект datetime.date.

        Args:
            date_str: Строка с датой в различных форматах

        Returns:
            Optional[date]: Объект даты или None
        """
        try:
            # Если это уже ISO формат YYYY-MM-DD
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                return datetime.strptime(date_str, '%Y-%m-%d').date()

            # Формат DD.MM.YYYY или DD/MM/YYYY
            match = re.search(r'(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{4})', date_str)
            if match:
                day, month, year = map(int, match.groups())
                return date(year, month, day)

            # Формат YYYY/MM/DD или YYYY.MM.DD
            match = re.search(r'(\d{4})[\/\.-](\d{1,2})[\/\.-](\d{1,2})', date_str)
            if match:
                year, month, day = map(int, match.groups())
                return date(year, month, day)

            # Формат DD.MM.YY или DD/MM/YY
            match = re.search(r'(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{2})', date_str)
            if match:
                day, month, year = map(int, match.groups())
                # Определяем век для двухзначного года
                if year < 50:
                    year += 2000
                else:
                    year += 1900
                return date(year, month, day)

            # Пробуем интерпретировать как Unix timestamp
            try:
                timestamp = int(date_str)
                return datetime.fromtimestamp(timestamp).date()
            except (ValueError, TypeError):
                pass

            # Пробуем другие распространенные форматы даты
            for fmt in ['%Y%m%d', '%d%m%Y', '%m%d%Y']:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue

            return None

        except Exception as e:
            logger.error(f"Ошибка при парсинге даты {date_str}: {str(e)}")
            return None

    def parse_time(self, time_str: str) -> Optional[time]:
        """
        Парсинг строки времени в объект datetime.time.

        Args:
            time_str: Строка с временем в различных форматах

        Returns:
            Optional[time]: Объект времени или None
        """
        try:
            # Если это уже ISO формат HH:MM:SS
            if re.match(r'^\d{2}:\d{2}(:\d{2})?$', time_str):
                if len(time_str) == 5:  # HH:MM
                    return datetime.strptime(time_str, '%H:%M').time()
                else:  # HH:MM:SS
                    return datetime.strptime(time_str, '%H:%M:%S').time()

            # Извлекаем часы, минуты и AM/PM
            match = self.time_pattern.search(time_str)
            if match:
                hour, minute, am_pm = match.groups()
                hour = int(hour)
                minute = int(minute)

                # Преобразуем 12-часовой формат в 24-часовой, если указано AM/PM
                if am_pm:
                    if am_pm.lower() == 'pm' and hour < 12:
                        hour += 12
                    elif am_pm.lower() == 'am' and hour == 12:
                        hour = 0

                return time(hour, minute)

            # Пробуем интерпретировать как количество минут с начала дня
            try:
                minutes = int(time_str)
                hour = minutes // 60
                minute = minutes % 60
                return time(hour, minute)
            except ValueError:
                pass

            return None

        except Exception as e:
            logger.error(f"Ошибка при парсинге времени {time_str}: {str(e)}")
            return None

    def clean_price(self, price_str: str) -> str:
        """
        Очистка строки с ценой от лишних символов.

        Args:
            price_str: Исходная строка с ценой

        Returns:
            str: Очищенная строка с ценой
        """
        try:
            # Удаляем пробелы из строки перед извлечением числового значения
            price_str_clean = price_str.replace(" ", "")

            # Извлекаем числовое значение цены
            match = self.price_pattern.search(price_str_clean)
            if match:
                price = match.group(1)
                # Находим валюту
                currency = None
                for c in ['₽', 'руб', 'р.', 'RUB', '$', 'USD', '€', 'EUR']:
                    if c in price_str:
                        currency = c
                        break

                # Форматируем результат
                if currency:
                    return f"{price} {currency}"
                else:
                    return price

            # Если не удалось извлечь, возвращаем исходную строку, очищенную от пробелов
            return price_str.strip()

        except Exception as e:
            logger.error(f"Ошибка при очистке цены {price_str}: {str(e)}")
            return price_str.strip()

    def extract_seat_number(self, text: str) -> str:
        """
        Извлечение номера места из строки.

        Args:
            text: Исходная строка с номером места

        Returns:
            str: Номер места
        """
        try:
            # Пробуем извлечь номер места из текста
            match = self.seat_pattern.search(text)
            if match:
                return match.group(1)

            # Если в тексте есть просто номер, возвращаем его
            if text.isdigit():
                return text

            # Пробуем найти любую цифру в тексте
            numbers = re.findall(r'\d+', text)
            if numbers:
                return numbers[0]

            # Если не удалось извлечь, возвращаем исходную строку
            return text.strip()

        except Exception as e:
            logger.error(f"Ошибка при извлечении номера места {text}: {str(e)}")
            return text.strip()

    async def extract_page_metadata(self, page: Page) -> Dict[str, Any]:
        """
        Извлечение метаданных страницы.

        Args:
            page: Страница браузера

        Returns:
            Dict[str, Any]: Словарь с метаданными страницы
        """
        try:
            metadata = {}

            # Получаем заголовок страницы
            metadata['title'] = await page.title()

            # Получаем URL страницы
            metadata['url'] = page.url

            # Получаем метатеги
            meta_tags = {}

            # Извлекаем все мета-теги
            meta_elements = await page.query_selector_all('meta')
            for meta in meta_elements:
                name = await self.extract_attribute(meta, 'name')
                content = await self.extract_attribute(meta, 'content')

                if name and content:
                    meta_tags[name] = content
                else:
                    # Проверяем property для Open Graph тегов
                    prop = await self.extract_attribute(meta, 'property')
                    if prop and content:
                        meta_tags[prop] = content

            metadata['meta_tags'] = meta_tags

            # Дополнительно извлекаем информацию о компании, если доступна
            company_info = {}

            # Имя компании из Open Graph или заголовка
            if 'og:site_name' in meta_tags:
                company_info['name'] = meta_tags['og:site_name']
            elif 'og:title' in meta_tags:
                company_info['name'] = meta_tags['og:title']

            # Описание компании
            if 'og:description' in meta_tags:
                company_info['description'] = meta_tags['og:description']
            elif 'description' in meta_tags:
                company_info['description'] = meta_tags['description']

            # Логотип компании
            if 'og:image' in meta_tags:
                company_info['logo'] = meta_tags['og:image']

            metadata['company_info'] = company_info

            return metadata

        except Exception as e:
            logger.error(f"Ошибка при извлечении метаданных страницы: {str(e)}")
            return {'url': page.url}