"""
FIXED Data Extractor - исправляет проблему парсинга времени как цены.
"""
import asyncio
import logging
import re
from datetime import datetime, time, date
from typing import Dict, List, Optional, Any, Tuple, Union

from playwright.async_api import ElementHandle, Page

logger = logging.getLogger(__name__)


class FixedDataExtractor:
    """
    ИСПРАВЛЕННЫЙ класс для извлечения данных с YClients.
    Основные исправления:
    1. НЕ извлекает время как цену
    2. Улучшенная валидация цен
    3. Лучшие селекторы для реального сайта YClients
    4. Контекстная проверка элементов
    """

    def __init__(self):
        """Инициализация экстрактора данных."""
        # Паттерны для проверки времени - СТРОГО
        self.time_patterns = [
            r'^\d{1,2}:\d{2}$',                    # 22:00, 7:30
            r'^\d{1,2}:\d{2}:\d{2}$',              # 22:00:00
            r'^\d{1,2}\s*:\s*\d{2}$',              # 22 : 00
        ]
        
        # Паттерны для цены - только с валютой
        self.price_patterns = [
            r'\d+\s*[₽]',                          # 1500₽, 1500 ₽
            r'\d+\s*(?:руб|рублей?)',              # 1500 руб, 1500 рублей
            r'\d+\s*(?:\$|USD)',                   # 1500$, 1500 USD
            r'\d+\s*(?:€|EUR)',                    # 1500€, 1500 EUR
        ]
        
        # Селекторы для ВРЕМЕНИ (чтобы исключать их при поиске цены)
        self.time_selectors = [
            '.time', '.slot-time', '.booking-time', '.schedule-time',
            '[data-time]', '.time-value', '.time-display',
            '.hour', '.minute', '.clock', '.duration'
        ]
        
        # Селекторы для ЦЕНЫ (исключаем временные элементы)
        self.price_selectors = [
            '[data-price]:not([data-time]):not(.time)',
            '.price:not(.time):not([data-time])',
            '.cost:not(.time)', '.amount:not(.time)', 
            '.service-price', '.booking-price', '.price-value',
            '.tariff', '.fee', '.rubles', '.currency'
        ]
        
        # Селекторы для ПРОВАЙДЕРА/СОТРУДНИКА
        self.provider_selectors = [
            '[data-staff-name]', '[data-staff]', '[data-specialist]',
            '.staff-name', '.specialist-name', '.master-name',
            '.employee-name', '.provider-name', '.worker-name'
        ]

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

    def is_definitely_time(self, text: str) -> bool:
        """Строгая проверка - является ли текст временем."""
        if not text:
            return False
        
        text = text.strip()
        
        # Проверяем точные паттерны времени
        for pattern in self.time_patterns:
            if re.match(pattern, text):
                return True
        
        return False

    def is_definitely_price(self, text: str) -> bool:
        """Строгая проверка - является ли текст ценой."""
        if not text:
            return False
        
        text = text.strip()
        
        # Если это время - точно НЕ цена
        if self.is_definitely_time(text):
            return False
        
        # Проверяем паттерны цены (только с валютой)
        for pattern in self.price_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False

    def is_probably_hour_from_time(self, text: str) -> bool:
        """Проверяет, является ли число вероятно часом из времени."""
        if not text:
            return False
        
        text = text.strip()
        
        # Если это просто число от 0 до 23 - вероятно час
        try:
            num = int(text)
            return 0 <= num <= 23
        except ValueError:
            return False

    async def is_element_time_related(self, element: ElementHandle) -> bool:
        """Проверяет, связан ли элемент со временем."""
        try:
            # Проверяем классы элемента
            class_name = await element.get_attribute('class') or ""
            if any(time_class in class_name.lower() for time_class in ['time', 'clock', 'hour', 'minute', 'duration']):
                return True
            
            # Проверяем атрибуты
            if await element.get_attribute('data-time'):
                return True
            
            # Проверяем родительские элементы
            parent = await element.query_selector('..')
            if parent:
                parent_class = await parent.get_attribute('class') or ""
                if any(time_class in parent_class.lower() for time_class in ['time', 'clock', 'schedule']):
                    return True
            
            return False
        except Exception:
            return False

    async def extract_price_fixed(self, slot_element: ElementHandle) -> Optional[str]:
        """
        ИСПРАВЛЕННОЕ извлечение цены - избегаем времени любой ценой.
        """
        logger.debug("🔍 Поиск цены (исправленный алгоритм)...")
        
        try:
            # 1. Ищем в специфических селекторах цены (исключая временные)
            for price_selector in self.price_selectors:
                try:
                    price_elements = await slot_element.query_selector_all(price_selector)
                    for price_element in price_elements:
                        # Проверяем, что элемент НЕ связан со временем
                        if await self.is_element_time_related(price_element):
                            logger.debug(f"🚫 Пропускаем элемент {price_selector} - связан со временем")
                            continue
                        
                        price_text = await self.extract_text_content(price_element)
                        if price_text and self.is_definitely_price(price_text):
                            cleaned = self.clean_price_strict(price_text)
                            if cleaned:
                                logger.info(f"✅ Найдена цена: {cleaned}")
                                return cleaned
                except Exception as e:
                    logger.debug(f"Ошибка в селекторе {price_selector}: {e}")
                    continue
            
            # 2. Ищем в атрибутах (только если НЕ время)
            price_attrs = ['data-price', 'data-cost', 'data-amount']
            for attr in price_attrs:
                if await slot_element.get_attribute('data-time'):
                    # Если есть data-time, пропускаем
                    continue
                    
                price_value = await self.extract_attribute(slot_element, attr)
                if price_value and self.is_definitely_price(price_value):
                    cleaned = self.clean_price_strict(price_value)
                    if cleaned:
                        logger.info(f"✅ Найдена цена в атрибуте {attr}: {cleaned}")
                        return cleaned
            
            # 3. Ищем в тексте элемента (очень осторожно)
            full_text = await self.extract_text_content(slot_element)
            if full_text:
                # Разбиваем на части и ищем цены с валютой
                parts = re.split(r'[\s\n\t]+', full_text)
                for part in parts:
                    if part and self.is_definitely_price(part):
                        # Дополнительная проверка - не час ли это
                        if not self.is_probably_hour_from_time(part.replace('₽', '').replace('руб', '').strip()):
                            cleaned = self.clean_price_strict(part)
                            if cleaned:
                                logger.info(f"✅ Найдена цена в тексте: {cleaned}")
                                return cleaned
            
            logger.debug("❌ Цена не найдена")
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка при извлечении цены: {str(e)}")
            return None

    def clean_price_strict(self, price_str: str) -> str:
        """СТРОГАЯ очистка цены - только с валютой."""
        if not price_str:
            return ""
        
        price_str = price_str.strip()
        
        # КРИТИЧНО: Если это время - возвращаем пустую строку
        if self.is_definitely_time(price_str):
            logger.warning(f"🚫 Отклоняем время как цену: {price_str}")
            return ""
        
        # КРИТИЧНО: Если это вероятно час из времени - отклоняем
        clean_number = re.sub(r'[₽руб$€]', '', price_str).strip()
        if self.is_probably_hour_from_time(clean_number):
            logger.warning(f"🚫 Отклоняем вероятный час: {price_str}")
            return ""
        
        # Ищем цену с валютой
        for pattern in self.price_patterns:
            if re.search(pattern, price_str, re.IGNORECASE):
                return price_str  # Возвращаем как есть, если есть валюта
        
        # НЕ добавляем валюту к голым числам - это может быть время!
        logger.warning(f"🚫 Отклоняем число без валюты: {price_str}")
        return ""

    async def extract_provider_fixed(self, slot_element: ElementHandle) -> str:
        """ИСПРАВЛЕННОЕ извлечение провайдера."""
        logger.debug("🔍 Поиск провайдера...")
        
        try:
            # 1. Ищем в специфических селекторах провайдера
            for provider_selector in self.provider_selectors:
                try:
                    provider_elements = await slot_element.query_selector_all(provider_selector)
                    for provider_element in provider_elements:
                        provider_text = await self.extract_text_content(provider_element)
                        if provider_text and self.is_valid_name(provider_text):
                            logger.info(f"✅ Найден провайдер: {provider_text}")
                            return provider_text.strip()
                except Exception:
                    continue
            
            # 2. Ищем в атрибутах
            provider_attrs = ['data-staff-name', 'data-provider', 'data-specialist']
            for attr in provider_attrs:
                provider_value = await self.extract_attribute(slot_element, attr)
                if provider_value and self.is_valid_name(provider_value):
                    logger.info(f"✅ Найден провайдер в атрибуте {attr}: {provider_value}")
                    return provider_value.strip()
            
            # 3. Ищем имена в тексте (очень осторожно)
            full_text = await self.extract_text_content(slot_element)
            if full_text:
                # Ищем паттерны имен
                name_patterns = [
                    r'\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\b',  # Русские ФИО
                    r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',       # Английские имена
                    r'\b[А-ЯЁ][а-яё]{2,}\b'                 # Одно русское имя
                ]
                
                for pattern in name_patterns:
                    matches = re.findall(pattern, full_text)
                    for match in matches:
                        if self.is_valid_name(match):
                            logger.info(f"✅ Найден провайдер в тексте: {match}")
                            return match.strip()
            
            logger.debug("❌ Провайдер не найден")
            return "Не указан"
            
        except Exception as e:
            logger.error(f"❌ Ошибка при извлечении провайдера: {str(e)}")
            return "Не указан"

    def is_valid_name(self, text: str) -> bool:
        """Проверяет валидность имени."""
        if not text or len(text.strip()) < 2:
            return False
        
        text = text.strip()
        
        # Исключаем числа, время, цены
        if re.search(r'^\d+$', text):
            return False
        if self.is_definitely_time(text):
            return False
        if re.search(r'[₽$€]', text):
            return False
        
        # Проверяем на валидное имя
        if re.match(r'^[А-ЯЁа-яёA-Za-z\s\-\.]+$', text):
            return True
        
        return False

    async def extract_time_fixed(self, slot_element: ElementHandle) -> Optional[str]:
        """ИСПРАВЛЕННОЕ извлечение времени."""
        logger.debug("🔍 Поиск времени...")
        
        try:
            # 1. Ищем в специфических селекторах времени
            for time_selector in self.time_selectors:
                try:
                    time_element = await slot_element.query_selector(time_selector)
                    if time_element:
                        time_text = await self.extract_text_content(time_element)
                        if time_text and self.is_definitely_time(time_text):
                            parsed_time = self.parse_time_safe(time_text)
                            if parsed_time:
                                logger.info(f"✅ Найдено время: {parsed_time}")
                                return parsed_time
                except Exception:
                    continue
            
            # 2. Ищем в атрибутах
            time_attrs = ['data-time', 'time']
            for attr in time_attrs:
                time_str = await self.extract_attribute(slot_element, attr)
                if time_str and self.is_definitely_time(time_str):
                    parsed_time = self.parse_time_safe(time_str)
                    if parsed_time:
                        logger.info(f"✅ Найдено время в атрибуте: {parsed_time}")
                        return parsed_time
            
            # 3. Ищем паттерны времени в тексте
            full_text = await self.extract_text_content(slot_element)
            if full_text:
                for pattern in self.time_patterns:
                    matches = re.findall(pattern, full_text)
                    for match in matches:
                        if self.is_definitely_time(match):
                            parsed_time = self.parse_time_safe(match)
                            if parsed_time:
                                logger.info(f"✅ Найдено время в тексте: {parsed_time}")
                                return parsed_time
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка при извлечении времени: {str(e)}")
            return None

    def parse_time_safe(self, time_str: str) -> Optional[str]:
        """Безопасный парсинг времени."""
        try:
            if re.match(r'^\d{1,2}:\d{2}$', time_str):
                parsed = datetime.strptime(time_str, '%H:%M').time()
                return parsed.isoformat()
            elif re.match(r'^\d{1,2}:\d{2}:\d{2}$', time_str):
                parsed = datetime.strptime(time_str, '%H:%M:%S').time()
                return parsed.isoformat()
            return None
        except Exception:
            return None

    async def extract_slot_data_fixed(self, slot_element: ElementHandle) -> Dict[str, Any]:
        """
        ИСПРАВЛЕННОЕ извлечение всех данных из слота.
        """
        try:
            result = {}

            # Извлекаем время (приоритет)
            time_str = await self.extract_time_fixed(slot_element)
            if time_str:
                result['time'] = time_str

            # Извлекаем цену (строгая проверка)
            price = await self.extract_price_fixed(slot_element)
            result['price'] = price if price else "Цена не найдена"

            # Извлекаем провайдера
            provider = await self.extract_provider_fixed(slot_element)
            result['provider'] = provider

            # Дополнительные метаданные
            result['extracted_at'] = datetime.now().isoformat()

            logger.info(f"📊 Извлечено: время={result.get('time', 'нет')}, цена={result.get('price')}, провайдер={result.get('provider')}")
            
            return result

        except Exception as e:
            logger.error(f"❌ Ошибка при извлечении данных: {str(e)}")
            return {}
