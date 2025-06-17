"""
Improved Data Extractor - ИСПРАВЛЕННАЯ версия для правильного парсинга цен и провайдеров.
"""
import asyncio
import logging
import re
from datetime import datetime, time, date
from typing import Dict, List, Optional, Any, Tuple, Union

from playwright.async_api import ElementHandle, Page
from src.parser.selectors import (
    SELECTORS, XPATH_SELECTORS, PATTERNS,
    is_time_not_price, is_price_not_time, is_valid_provider_name
)

logger = logging.getLogger(__name__)


class ImprovedDataExtractor:
    """
    ИСПРАВЛЕННЫЙ класс для извлечения данных.
    Основные исправления:
    - Предотвращение парсинга времени как цены
    - Улучшенное извлечение имен провайдеров
    - Надежная валидация данных
    """

    def __init__(self):
        """Инициализация экстрактора данных."""
        self.price_pattern = re.compile(PATTERNS["price"])
        self.price_number_pattern = re.compile(PATTERNS["price_number"])
        self.time_pattern = re.compile(PATTERNS["time"])
        self.name_pattern = re.compile(PATTERNS["name"])

    async def extract_text_content(self, element: ElementHandle) -> str:
        """Извлечение текстового содержимого элемента."""
        try:
            text = await element.text_content()
            return text.strip() if text else ""
        except Exception as e:
            logger.error(f"Ошибка при извлечении текста: {str(e)}")
            return ""

    async def extract_attribute(self, element: ElementHandle, attr: str) -> str:
        """Извлечение значения атрибута элемента."""
        try:
            value = await element.get_attribute(attr)
            return value.strip() if value else ""
        except Exception as e:
            logger.error(f"Ошибка при извлечении атрибута {attr}: {str(e)}")
            return ""

    async def extract_price_from_element_improved(self, element: ElementHandle) -> Optional[str]:
        """
        ИСПРАВЛЕННОЕ извлечение цены - избегаем парсинга времени как цены.
        """
        try:
            logger.debug("🔍 Поиск цены в элементе...")
            
            # 1. Ищем цену в специальных селекторах для цены
            for price_selector in SELECTORS["slot_price"]:
                try:
                    price_elements = await element.query_selector_all(price_selector)
                    for price_element in price_elements:
                        price_text = await self.extract_text_content(price_element)
                        if price_text and is_price_not_time(price_text):
                            cleaned_price = self.clean_price_enhanced(price_text)
                            if cleaned_price:
                                logger.info(f"✅ Найдена цена в {price_selector}: {cleaned_price}")
                                return cleaned_price
                except Exception:
                    continue
            
            # 2. Ищем в атрибутах
            price_attrs = ['data-price', 'data-cost', 'data-amount', 'price']
            for attr in price_attrs:
                price_value = await self.extract_attribute(element, attr)
                if price_value and is_price_not_time(price_value):
                    cleaned_price = self.clean_price_enhanced(price_value)
                    if cleaned_price:
                        logger.info(f"✅ Найдена цена в атрибуте {attr}: {cleaned_price}")
                        return cleaned_price
            
            # 3. Ищем через XPath
            try:
                for xpath in XPATH_SELECTORS["price_xpath"]:
                    price_texts = await element.evaluate(f"el => {{ const result = document.evaluate('{xpath}', el, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null); const texts = []; for(let i = 0; i < result.snapshotLength; i++) {{ texts.push(result.snapshotItem(i).textContent.trim()); }} return texts; }}")
                    for price_text in price_texts:
                        if price_text and is_price_not_time(price_text):
                            cleaned_price = self.clean_price_enhanced(price_text)
                            if cleaned_price:
                                logger.info(f"✅ Найдена цена через XPath: {cleaned_price}")
                                return cleaned_price
            except Exception as e:
                logger.debug(f"XPath для цены не сработал: {e}")
            
            # 4. Анализируем весь текст элемента, исключая время
            full_text = await self.extract_text_content(element)
            if full_text:
                # Разбиваем текст на части
                text_parts = re.split(r'[\s\n\t]+', full_text)
                for part in text_parts:
                    if part and is_price_not_time(part):
                        cleaned_price = self.clean_price_enhanced(part)
                        if cleaned_price:
                            logger.info(f"✅ Найдена цена в тексте: {cleaned_price}")
                            return cleaned_price
            
            logger.debug("❌ Цена не найдена")
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка при извлечении цены: {str(e)}")
            return None

    async def extract_provider_from_element_improved(self, element: ElementHandle) -> Optional[str]:
        """
        ИСПРАВЛЕННОЕ извлечение провайдера с валидацией имен.
        """
        try:
            logger.debug("🔍 Поиск провайдера в элементе...")
            
            # 1. Ищем провайдера в специальных селекторах
            for provider_selector in SELECTORS["slot_provider"]:
                try:
                    provider_elements = await element.query_selector_all(provider_selector)
                    for provider_element in provider_elements:
                        provider_text = await self.extract_text_content(provider_element)
                        if provider_text and is_valid_provider_name(provider_text):
                            logger.info(f"✅ Найден провайдер в {provider_selector}: {provider_text}")
                            return provider_text.strip()
                except Exception:
                    continue
            
            # 2. Ищем в атрибутах
            provider_attrs = ['data-staff-name', 'data-provider', 'data-specialist', 'staff-name']
            for attr in provider_attrs:
                provider_value = await self.extract_attribute(element, attr)
                if provider_value and is_valid_provider_name(provider_value):
                    logger.info(f"✅ Найден провайдер в атрибуте {attr}: {provider_value}")
                    return provider_value.strip()
            
            # 3. Ищем через XPath
            try:
                for xpath in XPATH_SELECTORS["provider_xpath"]:
                    provider_texts = await element.evaluate(f"el => {{ const result = document.evaluate('{xpath}', el, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null); const texts = []; for(let i = 0; i < result.snapshotLength; i++) {{ texts.push(result.snapshotItem(i).textContent.trim()); }} return texts; }}")
                    for provider_text in provider_texts:
                        if provider_text and is_valid_provider_name(provider_text):
                            logger.info(f"✅ Найден провайдер через XPath: {provider_text}")
                            return provider_text.strip()
            except Exception as e:
                logger.debug(f"XPath для провайдера не сработал: {e}")
            
            # 4. Анализируем весь текст элемента
            full_text = await self.extract_text_content(element)
            if full_text:
                # Ищем имена в тексте
                words = re.findall(r'[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)*|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', full_text)
                for word in words:
                    if is_valid_provider_name(word):
                        logger.info(f"✅ Найден провайдер в тексте: {word}")
                        return word.strip()
            
            logger.debug("❌ Провайдер не найден")
            return "Не указан"
            
        except Exception as e:
            logger.error(f"❌ Ошибка при извлечении провайдера: {str(e)}")
            return "Не указан"

    async def extract_time_from_element(self, element: ElementHandle) -> Optional[str]:
        """Извлечение времени из HTML-элемента."""
        try:
            logger.debug("🔍 Поиск времени в элементе...")
            
            # 1. Ищем время в специальных селекторах
            time_selectors = ['.time', '.slot-time', '.booking-time', '[data-time]']
            for time_selector in time_selectors:
                try:
                    time_element = await element.query_selector(time_selector)
                    if time_element:
                        time_text = await self.extract_text_content(time_element)
                        if time_text and is_time_not_price(time_text):
                            parsed_time = self.parse_time(time_text)
                            if parsed_time:
                                return parsed_time.isoformat()
                except Exception:
                    continue
            
            # 2. Ищем в атрибутах
            time_attrs = ['data-time', 'time']
            for attr in time_attrs:
                time_str = await self.extract_attribute(element, attr)
                if time_str and is_time_not_price(time_str):
                    parsed_time = self.parse_time(time_str)
                    if parsed_time:
                        return parsed_time.isoformat()
            
            # 3. Ищем в тексте элемента
            full_text = await self.extract_text_content(element)
            if full_text:
                # Ищем паттерн времени в тексте
                time_match = self.time_pattern.search(full_text)
                if time_match:
                    time_str = time_match.group(0)
                    if is_time_not_price(time_str):
                        parsed_time = self.parse_time(time_str)
                        if parsed_time:
                            return parsed_time.isoformat()
            
            return None

        except Exception as e:
            logger.error(f"❌ Ошибка при извлечении времени: {str(e)}")
            return None

    def clean_price_enhanced(self, price_str: str) -> str:
        """Улучшенная очистка и форматирование цены."""
        if not price_str:
            return ""
        
        price_str = ' '.join(price_str.split())
        
        # Проверяем, что это не время
        if is_time_not_price(price_str):
            return ""
        
        # Ищем цену с валютой
        currency_match = self.price_pattern.search(price_str)
        if currency_match:
            price_value = currency_match.group(1).replace(',', '.')
            currency = currency_match.group(2)
            return self.format_price_with_currency(price_value, currency)
        
        # Если просто число и контекст указывает на цену
        if self.price_number_pattern.match(price_str.strip()):
            return f"{price_str.strip()} ₽"
        
        return ""

    def format_price_with_currency(self, price: str, currency: str) -> str:
        """Форматирование цены с валютой."""
        currency_map = {
            '₽': '₽', 'руб': '₽', 'руб.': '₽', 'рублей': '₽', 'рубля': '₽', 'RUB': '₽',
            '$': '$', 'USD': '$', 'доллар': '$', 'долларов': '$',
            '€': '€', 'EUR': '€', 'евро': '€'
        }
        
        standardized_currency = currency_map.get(currency.lower(), currency)
        return f"{price} {standardized_currency}"

    def parse_time(self, time_str: str) -> Optional[time]:
        """Парсинг строки времени в объект datetime.time."""
        try:
            if re.match(r'^\d{2}:\d{2}(:\d{2})?$', time_str):
                if len(time_str) == 5:
                    return datetime.strptime(time_str, '%H:%M').time()
                else:
                    return datetime.strptime(time_str, '%H:%M:%S').time()

            match = self.time_pattern.search(time_str)
            if match:
                hour, minute, am_pm = match.groups()
                hour = int(hour)
                minute = int(minute)

                if am_pm:
                    if am_pm.lower() == 'pm' and hour < 12:
                        hour += 12
                    elif am_pm.lower() == 'am' and hour == 12:
                        hour = 0

                return time(hour, minute)

            return None

        except Exception as e:
            logger.error(f"Ошибка при парсинге времени {time_str}: {str(e)}")
            return None

    async def extract_booking_data_from_slot_improved(self, slot_element: ElementHandle) -> Dict[str, Any]:
        """
        ИСПРАВЛЕННОЕ извлечение всех данных бронирования из элемента слота.
        """
        try:
            result = {}

            # Извлекаем время
            time_str = await self.extract_time_from_element(slot_element)
            if time_str:
                result['time'] = time_str

            # Извлекаем цену (исправленный метод)
            price = await self.extract_price_from_element_improved(slot_element)
            if price:
                result['price'] = price
            else:
                result['price'] = "Не указано"

            # Извлекаем провайдера (исправленный метод)
            provider = await self.extract_provider_from_element_improved(slot_element)
            result['provider'] = provider

            # Дополнительные данные
            result['extracted_at'] = datetime.now().isoformat()

            logger.info(f"📊 Извлечены данные: время={result.get('time')}, цена={result.get('price')}, провайдер={result.get('provider')}")
            
            return result

        except Exception as e:
            logger.error(f"❌ Ошибка при извлечении данных из слота: {str(e)}")
            return {}
