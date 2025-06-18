"""
Database Manager - Стабильный менеджер для работы с Supabase в Docker окружении.
Исправленная версия для Timeweb деплоя.
"""
import asyncio
import logging
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Безопасный импорт Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Улучшенный менеджер базы данных для работы с Supabase.
    """
    
    def __init__(self):
        """Инициализация менеджера базы данных."""
        self.supabase: Optional[Client] = None
        self.is_initialized = False
        
        # Получаем настройки из переменных окружения
        self.supabase_url = os.environ.get("SUPABASE_URL", "")
        self.supabase_key = os.environ.get("SUPABASE_KEY", "")
        
        # Названия таблиц
        self.booking_table = "booking_data"
        self.url_table = "urls"
    
    async def initialize(self) -> None:
        """Инициализация подключения к Supabase."""
        try:
            if not SUPABASE_AVAILABLE:
                raise Exception("Supabase SDK не установлен")
            
            if not self.supabase_url or not self.supabase_key:
                raise Exception("SUPABASE_URL или SUPABASE_KEY не указаны")
            
            logger.info("🔗 Подключение к Supabase...")
            
            # Создаем клиент Supabase
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            
            # Проверяем подключение
            try:
                response = self.supabase.table(self.booking_table).select("id").limit(1).execute()
                logger.info("✅ Подключение к Supabase успешно")
            except Exception as e:
                logger.warning(f"⚠️ Таблица {self.booking_table} не найдена, создаем...")
                await self.create_tables_if_not_exist()
            
            self.is_initialized = True
            logger.info("✅ DatabaseManager инициализирован")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации DatabaseManager: {str(e)}")
            raise
    
    async def create_tables_if_not_exist(self) -> None:
        """Создание таблиц если они не существуют."""
        try:
            logger.info("🔨 Проверка и создание таблиц...")
            
            # SQL для создания таблицы booking_data
            booking_table_sql = """
            CREATE TABLE IF NOT EXISTS booking_data (
                id SERIAL PRIMARY KEY,
                url_id INTEGER,
                date DATE,
                time TIME,
                price TEXT,
                provider TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """
            
            # SQL для создания таблицы urls
            url_table_sql = """
            CREATE TABLE IF NOT EXISTS urls (
                id SERIAL PRIMARY KEY,
                url TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """
            
            # Выполняем SQL через Supabase (если поддерживается)
            # В противном случае таблицы должны быть созданы вручную
            logger.info("📋 Таблицы должны быть созданы в Supabase Dashboard")
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания таблиц: {str(e)}")
    
    async def save_booking_data(self, url: str, data: List[Dict[str, Any]]) -> bool:
        """
        Сохранение данных бронирования с улучшенной обработкой.
        """
        if not self.is_initialized:
            logger.error("❌ DatabaseManager не инициализирован")
            return False
        
        if not data:
            logger.warning("⚠️ Нет данных для сохранения")
            return True
        
        try:
            logger.info(f"💾 Сохранение {len(data)} записей для URL: {url}")
            
            # Получаем или создаем URL запись
            url_id = await self.get_or_create_url(url)
            
            # Подготавливаем данные для вставки
            records_to_insert = []
            
            for item in data:
                # Очищаем и валидируем данные
                cleaned_item = self.clean_booking_data(item)
                cleaned_item['url_id'] = url_id
                
                # Логируем что сохраняем
                logger.info(f"📝 Запись: дата={cleaned_item.get('date')}, время={cleaned_item.get('time')}, цена={cleaned_item.get('price')}, провайдер={cleaned_item.get('provider')}")
                
                records_to_insert.append(cleaned_item)
            
            # Вставляем данные батчами
            batch_size = 100
            total_inserted = 0
            
            for i in range(0, len(records_to_insert), batch_size):
                batch = records_to_insert[i:i + batch_size]
                
                try:
                    response = self.supabase.table(self.booking_table).insert(batch).execute()
                    
                    if response.data:
                        total_inserted += len(response.data)
                        logger.info(f"✅ Вставлен батч {i//batch_size + 1}: {len(response.data)} записей")
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка вставки батча {i//batch_size + 1}: {str(e)}")
                    
                    # Пробуем вставить записи по одной
                    for record in batch:
                        try:
                            response = self.supabase.table(self.booking_table).insert(record).execute()
                            if response.data:
                                total_inserted += 1
                        except Exception as single_error:
                            logger.error(f"❌ Ошибка вставки одной записи: {single_error}")
            
            logger.info(f"✅ Всего сохранено: {total_inserted} из {len(data)} записей")
            return total_inserted > 0
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения данных: {str(e)}")
            return False
    
    async def get_or_create_url(self, url: str) -> int:
        """Получение или создание URL записи."""
        try:
            # Ищем существующий URL
            response = self.supabase.table(self.url_table).select("id").eq("url", url).execute()
            
            if response.data:
                return response.data[0]['id']
            
            # Создаем новый URL
            response = self.supabase.table(self.url_table).insert({"url": url}).execute()
            
            if response.data:
                logger.info(f"✅ Создан новый URL: {url}")
                return response.data[0]['id']
            
            # Fallback: используем хеш URL как ID
            return hash(url) % 1000000
            
        except Exception as e:
            logger.error(f"❌ Ошибка работы с URL: {str(e)}")
            return hash(url) % 1000000
    
    def clean_booking_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Очистка и валидация данных бронирования.
        """
        cleaned = {}
        
        # Дата
        date_value = data.get('date', '')
        if date_value:
            try:
                # Если дата в формате строки, оставляем как есть
                if isinstance(date_value, str):
                    cleaned['date'] = date_value
                else:
                    cleaned['date'] = str(date_value)
            except:
                cleaned['date'] = None
        else:
            cleaned['date'] = None
        
        # Время
        time_value = data.get('time', '')
        if time_value:
            try:
                if isinstance(time_value, str):
                    cleaned['time'] = time_value
                else:
                    cleaned['time'] = str(time_value)
            except:
                cleaned['time'] = None
        else:
            cleaned['time'] = None
        
        # Цена - КРИТИЧЕСКИ ВАЖНО: проверяем что это не время!
        price_value = data.get('price', '')
        if price_value:
            price_str = str(price_value).strip()
            
            # Проверяем что это не время (формат HH:MM или просто число времени)
            if self.is_time_format(price_str):
                logger.warning(f"⚠️ Найдено время вместо цены: {price_str}")
                cleaned['price'] = "Цена не найдена"
            else:
                cleaned['price'] = price_str
        else:
            cleaned['price'] = "Цена не найдена"
        
        # Провайдер
        provider_value = data.get('provider', '')
        if provider_value and str(provider_value).strip() and str(provider_value).strip() != "Не указан":
            cleaned['provider'] = str(provider_value).strip()
        else:
            cleaned['provider'] = "Не указан"
        
        # Дополнительные поля
        cleaned['created_at'] = datetime.now().isoformat()
        
        return cleaned
    
    def is_time_format(self, value: str) -> bool:
        """Проверяет, является ли значение временем (УЛУЧШЕННАЯ ВЕРСИЯ)."""
        if not value:
            return False
        
        value = value.strip()
        
        # Проверяем формат времени HH:MM
        if ':' in value:
            parts = value.split(':')
            if len(parts) == 2:
                try:
                    hour, minute = int(parts[0]), int(parts[1])
                    return 0 <= hour <= 23 and 0 <= minute <= 59
                except ValueError:
                    return False
        
        # НОВОЕ: Проверяем если это число с валютой, но число соответствует часу
        # Это помогает поймать случаи "22₽", "7₽" и т.д.
        import re
        currency_number_match = re.match(r'^(\d+)\s*[₽Рруб$€]', value, re.IGNORECASE)
        if currency_number_match:
            try:
                num = int(currency_number_match.group(1))
                if 0 <= num <= 23:
                    return True  # Вероятно час с добавленной валютой
            except ValueError:
                pass
        
        # Проверяем если это просто число от 0 до 23 (час)
        try:
            num = int(value.replace('₽', '').replace('Р', '').replace('руб', '').strip())
            return 0 <= num <= 23
        except ValueError:
            return False
    
    async def get_booking_data(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Получение данных бронирования."""
        try:
            if not self.is_initialized:
                return []
            
            response = self.supabase.table(self.booking_table).select("*").range(offset, offset + limit - 1).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения данных: {str(e)}")
            return []
    
    async def close(self) -> None:
        """Закрытие соединения."""
        try:
            if self.supabase:
                # Supabase HTTP клиент не требует явного закрытия
                self.supabase = None
                self.is_initialized = False
                logger.info("✅ Соединение с Supabase закрыто")
        except Exception as e:
            logger.error(f"❌ Ошибка закрытия соединения: {str(e)}")
