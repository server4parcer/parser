"""
Improved Data Extractor - Исправленная версия для решения проблем с парсингом цены и провайдера.
"""
import asyncio
import logging
import re
from datetime import datetime, time, date
from typing import Dict, List, Optional, Any, Tuple, Union

from playwright.async_api import ElementHandle, Page

from src.parser.selectors import SELECTORS, XPATH_SELECTORS


logger = logging.getLogger(__name__)


class ImprovedDataExtractor:
    """
    Улучшенный класс для извлечения и обработки данных из HTML-элементов.
    Решает проблемы с извлечением цены и провайдера.
    """

    def __init__(self):
        """Инициализация экстрактора данных."""
        # Регулярные выражения для извлечения данных
        self.time_pattern = re.compile(r'(\d{1,2})[:\.](\d{2})(?:\s*(AM|PM|am|pm))?')
        self.price_pattern = re.compile(r'(\d+[\.,]?\d*)')
        self.price_with_currency_pattern = re.compile(r'(\d+[\.,]?\d*)\s*([₽$€]|руб\.?|рублей?|долларов?|USD|EUR|RUB)', re.IGNORECASE)
        self.currency_first_pattern = re.compile(r'([₽$€]|руб\.?|рублей?|долларов?|USD|EUR|RUB)\s*(\d+[\.,]?\d*)', re.IGNORECASE)
        self.name_pattern = re.compile(r'([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)*|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)')

    async def extract_text_content(self, element: ElementHandle) -> str:
        """Извлечение текстового содержимого элемента."""
        try:
            text = await element.text_content()
            return text.strip() if text else ""
        except Exception as e:
            logger.error(f"Ошибка при извлечении текстового содержимого: {str(e)}")
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
        Улучшенное извлечение цены из HTML-элемента.
        Решает проблему неполного извлечения цены.
        """
        try:
            # Расширенный список селекторов для цены
            price_selectors = [
                '.slot-price', '.price', '.service-price', '.booking-price',
                '.record__price', '.ycwidget-price', '[data-price]',
                '.cost', '.amount', '.fee', '.price-value', '.price-amount',
                '.booking-price-value', '.service-cost', '.slot-cost'
            ]
            
            # Пробуем найти цену в дочерних элементах
            for selector in price_selectors:
                price_element = await element.query_selector(selector)
                if price_element:
                    price_text = await self.extract_text_content(price_element)
                    if price_text:
                        cleaned_price = self.clean_price_enhanced(price_text)
                        if cleaned_price and cleaned_price != price_text.strip():
                            logger.info(f"Найдена цена в элементе {selector}: {cleaned_price}")
                            return cleaned_price

            # Проверяем атрибуты элемента
            price_attrs = ['data-price', 'data-cost', 'data-amount', 'price', 'cost', 'value']
            for attr in price_attrs:
                price_value = await self.extract_attribute(element, attr)
                if price_value and price_value.replace('.', '').replace(',', '').isdigit():
                    cleaned_price = self.clean_price_enhanced(price_value)
                    logger.info(f"Найдена цена в атрибуте {attr}: {cleaned_price}")
                    return cleaned_price

            # Анализируем весь текст элемента
            full_text = await self.extract_text_content(element)
            if full_text:
                cleaned_price = self.clean_price_enhanced(full_text)
                if cleaned_price:
                    logger.info(f"Найдена цена в тексте элемента: {cleaned_price}")
                    return cleaned_price

            return None
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении цены из элемента: {str(e)}")
            return None

    async def extract_provider_from_element_improved(self, element: ElementHandle) -> Optional[str]:
        """
        Улучшенное извлечение информации о провайдере из HTML-элемента.
        Решает проблему извлечения чисел вместо имен.
        """
        try:
            # Расширенный список селекторов для провайдера
            provider_selectors = [
                '.slot-provider', '.provider-name', '.staff-name', '.booking-provider',
                '.record__staff', '.ycwidget-staff', '[data-staff]', '[data-provider]',
                '.specialist-name', '.master-name', '.employee-name',
                '.staff-info .name', '.provider-info .name', '.master', '.specialist',
                '.staff-member', '.employee', '.worker'
            ]
            
            # Пробуем найти провайдера в дочерних элементах
            for selector in provider_selectors:
                provider_element = await element.query_selector(selector)
                if provider_element:
                    provider_text = await self.extract_text_content(provider_element)
                    if provider_text and self.is_valid_name(provider_text):
                        logger.info(f"Найден провайдер в элементе {selector}: {provider_text}")
                        return provider_text.strip()

            # Проверяем атрибуты
            provider_attrs = ['data-staff', 'data-provider', 'data-specialist', 'staff-name', 'provider-name']
            for attr in provider_attrs:
                provider_value = await self.extract_attribute(element, attr)
                if provider_value and self.is_valid_name(provider_value):
                    logger.info(f"Найден провайдер в атрибуте {attr}: {provider_value}")
                    return provider_value.strip()

            # Анализируем текст элемента для извлечения имени
            full_text = await self.extract_text_content(element)
            if full_text:
                extracted_name = self.extract_name_from_text(full_text)
                if extracted_name:
                    logger.info(f"Найден провайдер в тексте элемента: {extracted_name}")
                    return extracted_name

            return "Не указан"
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении провайдера из элемента: {str(e)}")
            return "Не указан"

    def clean_price_enhanced(self, price_str: str) -> str:
        """Улучшенная очистка и форматирование цены."""
        if not price_str:
            return ""
        
        # Удаляем лишние пробелы и переносы строк
        price_str = ' '.join(price_str.split())
        
        # Сначала пробуем найти цену с валютой
        currency_match = self.price_with_currency_pattern.search(price_str)
        if currency_match:
            price_value = currency_match.group(1).replace(',', '.')
            currency = currency_match.group(2)
            return self.format_price_with_currency(price_value, currency)
        
        # Пробуем найти валюту в начале
        currency_first_match = self.currency_first_pattern.search(price_str)
        if currency_first_match:
            currency = currency_first_match.group(1)
            price_value = currency_first_match.group(2).replace(',', '.')
            return self.format_price_with_currency(price_value, currency)
        
        # Если не удалось найти валюту, ищем просто число
        number_match = self.price_pattern.search(price_str)
        if number_match:
            price_value = number_match.group(1).replace(',', '.')
            # Проверяем, есть ли в тексте индикаторы валюты
            if any(curr in price_str.lower() for curr in ['₽', 'руб', 'rub', 'рублей', 'рубля']):
                return f"{price_value} ₽"
            elif any(curr in price_str.lower() for curr in ['$', 'usd', 'доллар']):
                return f"{price_value} $"
            elif any(curr in price_str.lower() for curr in ['€', 'eur', 'евро']):
                return f"{price_value} €"
            else:
                # По умолчанию рубли для российского сервиса
                return f"{price_value} ₽"
        
        return ""

    def format_price_with_currency(self, price: str, currency: str) -> str:
        """Форматирование цены с валютой."""
        # Стандартизация валют
        currency_map = {
            '₽': '₽', 'руб': '₽', 'руб.': '₽', 'рублей': '₽', 'рубля': '₽', 'RUB': '₽',
            '$': '$', 'USD': '$', 'доллар': '$', 'долларов': '$',
            '€': '€', 'EUR': '€', 'евро': '€'
        }
        
        standardized_currency = currency_map.get(currency.lower(), currency)
        return f"{price} {standardized_currency}"

    def is_valid_name(self, text: str) -> bool:
        """Проверяет, является ли текст валидным именем (не числом)."""
        if not text or len(text.strip()) < 2:
            return False
        
        text = text.strip()
        
        # Исключаем числа
        if text.isdigit() or text.replace('.', '').replace(',', '').isdigit():
            return False
        
        # Исключаем цены
        if re.search(r'\d+.*[₽$€]', text) or re.search(r'[₽$€].*\d+', text):
            return False
        
        # Проверяем на наличие букв
        if not re.search(r'[А-Яа-яA-Za-z]', text):
            return False
        
        # Исключаем слишком короткие "имена"
        if len(text) < 2:
            return False
        
        return True

    def extract_name_from_text(self, text: str) -> Optional[str]:
        """Извлекает имя из текста, исключая числа и цены."""
        if not text:
            return None
        
        # Убираем цены из текста
        text_without_prices = re.sub(r'\d+[\.,]?\d*\s*[₽$€руб]', '', text, flags=re.IGNORECASE)
        text_without_prices = re.sub(r'[₽$€руб]\s*\d+[\.,]?\d*', '', text_without_prices, flags=re.IGNORECASE)
        
        # Ищем имена в тексте
        name_matches = self.name_pattern.findall(text_without_prices)
        
        for name in name_matches:
            if self.is_valid_name(name):
                return name.strip()
        
        # Если не нашли имя паттерном, пробуем другие подходы
        # Ищем текст после двоеточия (часто так обозначают имена)
        if ':' in text:
            parts = text.split(':')
            for part in parts:
                part = part.strip()
                if self.is_valid_name(part):
                    return part
        
        return None

    async def extract_booking_data_from_slot_improved(self, slot_element: ElementHandle) -> Dict[str, Any]:
        """Улучшенное извлечение всех данных бронирования из элемента слота."""
        try:
            result = {}

            # Извлекаем время
            time_str = await self.extract_time_from_element(slot_element)
            if time_str:
                result['time'] = time_str

            # Извлекаем цену (улучшенный метод)
            price = await self.extract_price_from_element_improved(slot_element)
            if price:
                result['price'] = price
            else:
                result['price'] = "Не указано"

            # Извлекаем провайдера (улучшенный метод)
            provider = await self.extract_provider_from_element_improved(slot_element)
            if provider:
                result['provider'] = provider
            else:
                result['provider'] = "Не указан"

            # Дополнительные данные
            result['extracted_at'] = datetime.now().isoformat()

            logger.info(f"Извлечены данные: время={result.get('time')}, цена={result.get('price')}, провайдер={result.get('provider')}")
            
            return result

        except Exception as e:
            logger.error(f"Ошибка при извлечении данных из слота: {str(e)}")
            return {}

    async def extract_time_from_element(self, element: ElementHandle) -> Optional[str]:
        """Извлечение времени из HTML-элемента."""
        try:
            # Селекторы для времени
            time_selectors = ['.time', '.slot-time', '.booking-time', '[data-time]']
            
            for selector in time_selectors:
                time_element = await element.query_selector(selector)
                if time_element:
                    time_text = await self.extract_text_content(time_element)
                    if time_text:
                        parsed_time = self.parse_time(time_text)
                        if parsed_time:
                            return parsed_time.isoformat()

            # Проверяем атрибуты
            time_attrs = ['data-time', 'time', 'value']
            for attr in time_attrs:
                time_str = await self.extract_attribute(element, attr)
                if time_str:
                    parsed_time = self.parse_time(time_str)
                    if parsed_time:
                        return parsed_time.isoformat()

            # Анализируем весь текст элемента
            full_text = await self.extract_text_content(element)
            if full_text:
                parsed_time = self.parse_time(full_text)
                if parsed_time:
                    return parsed_time.isoformat()

            return None

        except Exception as e:
            logger.error(f"Ошибка при извлечении времени из элемента: {str(e)}")
            return None

    def parse_time(self, time_str: str) -> Optional[time]:
        """Парсинг строки времени в объект datetime.time."""
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

                # Преобразуем 12-часовой формат в 24-часовой
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
