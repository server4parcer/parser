"""
Database Manager - Управление подключением к базе данных и операции с данными.

Модуль предоставляет интерфейс для работы с PostgreSQL через Supabase.
"""
import asyncio
import logging
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

import asyncpg
from supabase import create_client, Client
try:
    from postgrest.types import CountMethod as Count
except ImportError:
    # Define a simple Count class as a fallback
    class Count:
        def __init__(self, column="*"):
            self.column = column
        
        def __str__(self):
            return f"count({self.column})"

from config.settings import (
    SUPABASE_URL,
    SUPABASE_KEY,
    PG_CONNECTION_STRING,
    BOOKING_TABLE,
    URL_TABLE,
    EXPORT_PATH
)


logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Менеджер базы данных для работы с PostgreSQL через Supabase.
    """
    
    def __init__(self):
        """Инициализация менеджера базы данных."""
        self.supabase: Optional[Client] = None
        self.pool: Optional[asyncpg.Pool] = None
        self.is_initialized = False
    
    async def initialize(self) -> None:
        """Инициализация соединения с базой данных."""
        try:
            # Инициализация клиента Supabase
            self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # Создаем пул соединений PostgreSQL для прямых запросов
            self.pool = await asyncpg.create_pool(PG_CONNECTION_STRING)
            
            # Проверяем соединение
            await self._check_connection()
            
            # Проверяем структуру таблиц
            await self._check_tables()
            
            self.is_initialized = True
            logger.info("Соединение с базой данных успешно инициализировано")
        
        except Exception as e:
            logger.error(f"Ошибка при инициализации соединения с базой данных: {str(e)}")
            # Если есть открытый пул, закрываем его
            if self.pool:
                await self.pool.close()
            
            self.is_initialized = False
            raise
    
    async def close(self) -> None:
        """Закрытие соединения с базой данных."""
        try:
            if self.pool:
                await self.pool.close()
                logger.info("Соединение с базой данных закрыто")
        
        except Exception as e:
            logger.error(f"Ошибка при закрытии соединения с базой данных: {str(e)}")
    
    async def _check_connection(self) -> None:
        """Проверка соединения с базой данных."""
        try:
            # Проверяем доступ к Supabase
            response = await self.supabase.auth.get_user()
            
            # Проверяем прямое соединение с PostgreSQL
            async with self.pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                logger.info(f"Соединение с PostgreSQL установлено: {version}")
            
        except Exception as e:
            logger.error(f"Ошибка при проверке соединения с базой данных: {str(e)}")
            raise
    
    async def _check_tables(self) -> None:
        """Проверка структуры таблиц и их создание при необходимости."""
        try:
            async with self.pool.acquire() as conn:
                # Проверяем существование таблицы с URL
                url_table_exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = $1)",
                    URL_TABLE
                )
                
                # Создаем таблицу URL, если она не существует
                if not url_table_exists:
                    logger.info(f"Создание таблицы {URL_TABLE}")
                    await conn.execute(f"""
                        CREATE TABLE {URL_TABLE} (
                            id SERIAL PRIMARY KEY,
                            url TEXT UNIQUE NOT NULL,
                            title TEXT,
                            description TEXT,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            is_active BOOLEAN DEFAULT TRUE
                        )
                    """)
                
                # Проверяем существование таблицы с данными бронирования
                booking_table_exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = $1)",
                    BOOKING_TABLE
                )
                
                # Создаем таблицу данных бронирования, если она не существует
                if not booking_table_exists:
                    logger.info(f"Создание таблицы {BOOKING_TABLE}")
                    await conn.execute(f"""
                        CREATE TABLE {BOOKING_TABLE} (
                            id SERIAL PRIMARY KEY,
                            url_id INTEGER REFERENCES {URL_TABLE}(id),
                            date DATE NOT NULL,
                            time TIME NOT NULL,
                            price TEXT,
                            provider TEXT,
                            seat_number TEXT,
                            extra_data JSONB,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(url_id, date, time, seat_number)
                        )
                    """)
                    
                    # Индекс для быстрого поиска по url_id и date
                    await conn.execute(f"""
                        CREATE INDEX {BOOKING_TABLE}_url_id_date_idx 
                        ON {BOOKING_TABLE}(url_id, date)
                    """)
                
                logger.info("Проверка структуры таблиц завершена")
        
        except Exception as e:
            logger.error(f"Ошибка при проверке структуры таблиц: {str(e)}")
            raise
    
    async def get_or_create_url(self, url: str, title: str = None, description: str = None) -> int:
        """
        Получение ID URL из базы данных или создание новой записи.
        
        Args:
            url: URL страницы
            title: Заголовок страницы (опционально)
            description: Описание страницы (опционально)
            
        Returns:
            int: ID URL в базе данных
        """
        try:
            # Пытаемся найти URL в базе данных
            async with self.pool.acquire() as conn:
                url_id = await conn.fetchval(
                    f"SELECT id FROM {URL_TABLE} WHERE url = $1",
                    url
                )
                
                # Если URL не найден, создаем новую запись
                if url_id is None:
                    logger.info(f"Создание новой записи для URL: {url}")
                    url_id = await conn.fetchval(
                        f"""
                        INSERT INTO {URL_TABLE} (url, title, description)
                        VALUES ($1, $2, $3)
                        RETURNING id
                        """,
                        url, title, description
                    )
                
                # Обновляем updated_at
                await conn.execute(
                    f"UPDATE {URL_TABLE} SET updated_at = CURRENT_TIMESTAMP WHERE id = $1",
                    url_id
                )
                
                return url_id
        
        except Exception as e:
            logger.error(f"Ошибка при получении или создании URL {url}: {str(e)}")
            raise
    
    async def save_booking_data(self, url: str, booking_data: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Сохранение данных бронирования в базу данных с поддержкой бизнес-аналитики.
        
        Args:
            url: URL страницы
            booking_data: Список словарей с данными бронирования
            
        Returns:
            Tuple[int, int]: (Количество новых записей, количество обновленных записей)
        """
        if not booking_data:
            logger.warning(f"Нет данных для сохранения для URL {url}")
            return 0, 0
        
        try:
            # Получаем ID URL
            url_id = await self.get_or_create_url(url)
            
            # Счетчики для новых и обновленных записей
            new_count = 0
            updated_count = 0
            
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Получаем все существующие записи для этого URL с датой и временем
                    existing_bookings = await conn.fetch(
                        f"""
                        SELECT date, time, seat_number, id, price
                        FROM {BOOKING_TABLE}
                        WHERE url_id = $1
                        """,
                        url_id
                    )
                    
                    # Создаем словарь для быстрого поиска существующих записей
                    existing_dict = {
                        (row['date'].isoformat(), row['time'].isoformat(), row['seat_number']): {
                            'id': row['id'],
                            'price': row['price']
                        }
                        for row in existing_bookings
                    }
                    
                    # Обрабатываем каждую запись
                    for data in booking_data:
                        # Получаем основные поля
                        date_str = data.get('date')
                        time_str = data.get('time')
                        price = data.get('price')
                        provider = data.get('provider')
                        seat_number = data.get('seat_number')
                        
                        # Получаем новые поля для бизнес-аналитики
                        location_name = data.get('location_name')
                        court_type = data.get('court_type')
                        time_category = data.get('time_category')
                        duration = data.get('duration')
                        review_count = data.get('review_count')
                        prepayment_required = data.get('prepayment_required', False)
                        raw_venue_data = data.get('raw_venue_data')
                        
                        # Пропускаем записи без основных полей
                        if not date_str or not time_str:
                            logger.warning(f"Пропускаем запись без даты или времени: {data}")
                            continue
                        
                        # Преобразуем строки в объекты даты и времени
                        try:
                            # Подготавливаем дату
                            date_obj = await self._parse_date(date_str)
                            
                            # Подготавливаем время
                            time_obj = await self._parse_time(time_str)
                            
                            # Дополнительные данные (все, что не входит в основные поля)
                            extra_data = {k: v for k, v in data.items() 
                                        if k not in [
                                            'date', 'time', 'price', 'provider', 'seat_number',
                                            'location_name', 'court_type', 'time_category', 
                                            'duration', 'review_count', 'prepayment_required',
                                            'raw_venue_data'
                                        ]}
                            
                            # Проверяем, существует ли уже такая запись
                            key = (date_obj.isoformat(), time_obj.isoformat(), seat_number)
                            
                            if key in existing_dict:
                                # Получаем ID существующей записи
                                booking_id = existing_dict[key]['id']
                                old_price = existing_dict[key]['price']
                                
                                # Если цена изменилась, записываем в историю цен
                                if price and old_price and price != old_price:
                                    await conn.execute(
                                        """
                                        INSERT INTO price_history (booking_data_id, price)
                                        VALUES ($1, $2)
                                        ON CONFLICT (booking_data_id, recorded_at) DO NOTHING
                                        """,
                                        booking_id, old_price
                                    )
                                
                                # Обновляем существующую запись
                                await conn.execute(
                                    f"""
                                    UPDATE {BOOKING_TABLE}
                                    SET price = $1, provider = $2, location_name = $3, 
                                        court_type = $4, time_category = $5, duration = $6,
                                        review_count = $7, prepayment_required = $8,
                                        raw_venue_data = $9, extra_data = $10,
                                        updated_at = CURRENT_TIMESTAMP
                                    WHERE id = $11
                                    """,
                                    price, provider, location_name, court_type, time_category,
                                    duration, review_count, prepayment_required,
                                    json.dumps(raw_venue_data) if raw_venue_data else None,
                                    json.dumps(extra_data) if extra_data else None,
                                    booking_id
                                )
                                updated_count += 1
                            else:
                                # Добавляем новую запись
                                booking_id = await conn.fetchval(
                                    f"""
                                    INSERT INTO {BOOKING_TABLE}
                                    (url_id, date, time, price, provider, seat_number, location_name,
                                     court_type, time_category, duration, review_count, 
                                     prepayment_required, raw_venue_data, extra_data)
                                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                                    RETURNING id
                                    """,
                                    url_id, date_obj, time_obj, price, provider, seat_number,
                                    location_name, court_type, time_category, duration,
                                    review_count, prepayment_required,
                                    json.dumps(raw_venue_data) if raw_venue_data else None,
                                    json.dumps(extra_data) if extra_data else None
                                )
                                new_count += 1
                        
                        except Exception as e:
                            logger.error(f"Ошибка при обработке записи {data}: {str(e)}")
            
            logger.info(f"Сохранено {new_count} новых и обновлено {updated_count} записей для URL {url}")
            return new_count, updated_count
        
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных бронирования для URL {url}: {str(e)}")
            raise
    
    async def get_booking_data(
        self, 
        url: str = None, 
        date_from: str = None, 
        date_to: str = None,
        location_name: str = None,
        court_type: str = None,
        time_category: str = None
    ) -> List[Dict[str, Any]]:
        """
        Получение данных бронирования из базы данных с поддержкой новых фильтров.
        
        Args:
            url: URL страницы (опционально)
            date_from: Начальная дата в формате YYYY-MM-DD (опционально)
            date_to: Конечная дата в формате YYYY-MM-DD (опционально)
            location_name: Название локации (опционально)
            court_type: Тип корта (опционально)
            time_category: Категория времени (опционально)
            
        Returns:
            List[Dict[str, Any]]: Список словарей с данными бронирования
        """
        try:
            query = f"""
                SELECT b.id, u.url, b.date, b.time, b.price, b.provider, b.seat_number, 
                       b.location_name, b.court_type, b.time_category, b.duration, 
                       b.review_count, b.prepayment_required, b.raw_venue_data,
                       b.extra_data, b.created_at, b.updated_at
                FROM {BOOKING_TABLE} b
                JOIN {URL_TABLE} u ON b.url_id = u.id
                WHERE 1=1
            """
            params = []
            
            # Добавляем фильтр по URL
            if url:
                query += f" AND u.url = ${len(params) + 1}"
                params.append(url)
            
            # Добавляем фильтр по начальной дате
            if date_from:
                query += f" AND b.date >= ${len(params) + 1}"
                params.append(await self._parse_date(date_from))
            
            # Добавляем фильтр по конечной дате
            if date_to:
                query += f" AND b.date <= ${len(params) + 1}"
                params.append(await self._parse_date(date_to))
            
            # Добавляем новые фильтры
            if location_name:
                query += f" AND b.location_name = ${len(params) + 1}"
                params.append(location_name)
            
            if court_type:
                query += f" AND b.court_type = ${len(params) + 1}"
                params.append(court_type)
            
            if time_category:
                query += f" AND b.time_category = ${len(params) + 1}"
                params.append(time_category)
            
            # Сортировка
            query += " ORDER BY b.date, b.time"
            
            # Выполняем запрос
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
            
            # Преобразуем результаты в список словарей
            result = []
            for row in rows:
                data = {
                    'id': row['id'],
                    'url': row['url'],
                    'date': row['date'].isoformat(),
                    'time': row['time'].isoformat(),
                    'price': row['price'],
                    'provider': row['provider'],
                    'seat_number': row['seat_number'],
                    'location_name': row['location_name'],
                    'court_type': row['court_type'],
                    'time_category': row['time_category'],
                    'duration': row['duration'],
                    'review_count': row['review_count'],
                    'prepayment_required': row['prepayment_required'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None
                }
                
                # Добавляем сырые данные о площадке, если они есть
                if row['raw_venue_data']:
                    data['raw_venue_data'] = json.loads(row['raw_venue_data'])
                
                # Добавляем дополнительные данные, если они есть
                if row['extra_data']:
                    extra_data = json.loads(row['extra_data'])
                    data.update(extra_data)
                
                result.append(data)
            
            logger.info(f"Получено {len(result)} записей бронирования")
            return result
        
        except Exception as e:
            logger.error(f"Ошибка при получении данных бронирования: {str(e)}")
            return []
    
    async def export_to_csv(
        self, 
        filepath: str = None, 
        url: str = None, 
        date_from: str = None, 
        date_to: str = None,
        location_name: str = None,
        court_type: str = None,
        time_category: str = None
    ) -> str:
        """
        Экспорт данных бронирования в CSV файл с поддержкой новых фильтров.
        
        Args:
            filepath: Путь к файлу для сохранения (опционально)
            url: URL страницы (опционально)
            date_from: Начальная дата в формате YYYY-MM-DD (опционально)
            date_to: Конечная дата в формате YYYY-MM-DD (опционально)
            location_name: Название локации (опционально)
            court_type: Тип корта (опционально)
            time_category: Категория времени (опционально)
            
        Returns:
            str: Путь к созданному файлу
        """
        try:
            # Получаем данные
            data = await self.get_booking_data(
                url=url, 
                date_from=date_from, 
                date_to=date_to,
                location_name=location_name,
                court_type=court_type,
                time_category=time_category
            )
            
            if not data:
                logger.warning("Нет данных для экспорта в CSV")
                return ""
            
            # Если путь не указан, создаем стандартный
            if not filepath:
                os.makedirs(EXPORT_PATH, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = os.path.join(EXPORT_PATH, f"booking_data_{timestamp}.csv")
            
            # Определяем основные и новые заголовки бизнес-аналитики
            headers = set([
                'id', 'url', 'date', 'time', 'price', 'provider', 'seat_number', 
                'location_name', 'court_type', 'time_category', 'duration', 
                'review_count', 'prepayment_required', 'created_at', 'updated_at'
            ])
            
            # Добавляем все остальные ключи из данных
            for item in data:
                headers.update(item.keys())
            
            # Исключаем сырые данные из CSV, т.к. они могут быть большими и сложными
            headers.discard('raw_venue_data')
            
            headers = sorted(list(headers))
            
            # Экспортируем данные в CSV
            import csv
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                
                # Подготавливаем данные для записи
                clean_data = []
                for item in data:
                    # Создаем копию элемента без raw_venue_data
                    clean_item = {k: v for k, v in item.items() if k != 'raw_venue_data'}
                    clean_data.append(clean_item)
                
                writer.writerows(clean_data)
            
            logger.info(f"Данные экспортированы в CSV: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Ошибка при экспорте данных в CSV: {str(e)}")
            return ""
    
    async def export_to_json(
        self, 
        filepath: str = None, 
        url: str = None, 
        date_from: str = None, 
        date_to: str = None,
        location_name: str = None,
        court_type: str = None,
        time_category: str = None,
        include_raw_data: bool = False
    ) -> str:
        """
        Экспорт данных бронирования в JSON файл с поддержкой новых фильтров.
        
        Args:
            filepath: Путь к файлу для сохранения (опционально)
            url: URL страницы (опционально)
            date_from: Начальная дата в формате YYYY-MM-DD (опционально)
            date_to: Конечная дата в формате YYYY-MM-DD (опционально)
            location_name: Название локации (опционально)
            court_type: Тип корта (опционально)
            time_category: Категория времени (опционально)
            include_raw_data: Включить сырые данные о площадке в экспорт (по умолчанию False)
            
        Returns:
            str: Путь к созданному файлу
        """
        try:
            # Получаем данные
            data = await self.get_booking_data(
                url=url, 
                date_from=date_from, 
                date_to=date_to,
                location_name=location_name,
                court_type=court_type,
                time_category=time_category
            )
            
            if not data:
                logger.warning("Нет данных для экспорта в JSON")
                return ""
            
            # Если путь не указан, создаем стандартный
            if not filepath:
                os.makedirs(EXPORT_PATH, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = os.path.join(EXPORT_PATH, f"booking_data_{timestamp}.json")
            
            # Если не нужно включать сырые данные, удаляем их
            if not include_raw_data:
                for item in data:
                    if 'raw_venue_data' in item:
                        del item['raw_venue_data']
            
            # Экспортируем данные в JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Данные экспортированы в JSON: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Ошибка при экспорте данных в JSON: {str(e)}")
            return ""
    
    async def delete_old_data(self, days: int = 30) -> int:
        """
        Удаление устаревших данных из базы данных.
        
        Args:
            days: Количество дней, после которых данные считаются устаревшими
            
        Returns:
            int: Количество удаленных записей
        """
        try:
            async with self.pool.acquire() as conn:
                # Удаляем устаревшие данные
                result = await conn.execute(
                    f"""
                    DELETE FROM {BOOKING_TABLE}
                    WHERE date < CURRENT_DATE - $1::interval
                    """,
                    f"{days} days"
                )
                
                # Получаем количество удаленных записей
                count = int(result.split(" ")[-1])
                logger.info(f"Удалено {count} устаревших записей")
                return count
        
        except Exception as e:
            logger.error(f"Ошибка при удалении устаревших данных: {str(e)}")
            return 0
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики по данным бронирования.
        
        Returns:
            Dict[str, Any]: Словарь со статистикой
        """
        try:
            async with self.pool.acquire() as conn:
                # Количество URL
                url_count = await conn.fetchval(
                    f"SELECT COUNT(*) FROM {URL_TABLE}"
                )
                
                # Количество записей
                booking_count = await conn.fetchval(
                    f"SELECT COUNT(*) FROM {BOOKING_TABLE}"
                )
                
                # Количество записей по датам
                date_stats = await conn.fetch(
                    f"""
                    SELECT date, COUNT(*) as count
                    FROM {BOOKING_TABLE}
                    GROUP BY date
                    ORDER BY date DESC
                    LIMIT 10
                    """
                )
                
                # Количество записей по URL
                url_stats = await conn.fetch(
                    f"""
                    SELECT u.url, COUNT(b.id) as count
                    FROM {URL_TABLE} u
                    LEFT JOIN {BOOKING_TABLE} b ON u.id = b.url_id
                    GROUP BY u.id, u.url
                    ORDER BY count DESC
                    """
                )
                
                # Новая статистика по типам кортов
                court_type_stats = await conn.fetch(
                    f"""
                    SELECT court_type, COUNT(*) as count
                    FROM {BOOKING_TABLE}
                    WHERE court_type IS NOT NULL
                    GROUP BY court_type
                    ORDER BY count DESC
                    """
                )
                
                # Новая статистика по категориям времени
                time_category_stats = await conn.fetch(
                    f"""
                    SELECT time_category, COUNT(*) as count
                    FROM {BOOKING_TABLE}
                    WHERE time_category IS NOT NULL
                    GROUP BY time_category
                    ORDER BY count DESC
                    """
                )
                
                # Новая статистика по локациям
                location_stats = await conn.fetch(
                    f"""
                    SELECT location_name, COUNT(*) as count
                    FROM {BOOKING_TABLE}
                    WHERE location_name IS NOT NULL
                    GROUP BY location_name
                    ORDER BY count DESC
                    """
                )
                
                # Формируем результат
                result = {
                    'url_count': url_count,
                    'booking_count': booking_count,
                    'date_stats': [
                        {
                            'date': row['date'].isoformat(),
                            'count': row['count']
                        }
                        for row in date_stats
                    ],
                    'url_stats': [
                        {
                            'url': row['url'],
                            'count': row['count']
                        }
                        for row in url_stats
                    ],
                    'court_type_stats': [
                        {
                            'court_type': row['court_type'],
                            'count': row['count']
                        }
                        for row in court_type_stats
                    ],
                    'time_category_stats': [
                        {
                            'time_category': row['time_category'],
                            'count': row['count']
                        }
                        for row in time_category_stats
                    ],
                    'location_stats': [
                        {
                            'location_name': row['location_name'],
                            'count': row['count']
                        }
                        for row in location_stats
                    ]
                }
                
                return result
        
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {str(e)}")
            return {
                'url_count': 0,
                'booking_count': 0,
                'date_stats': [],
                'url_stats': [],
                'court_type_stats': [],
                'time_category_stats': [],
                'location_stats': []
            }
    
    async def _parse_date(self, date_str: str) -> datetime.date:
        """
        Парсинг строки даты в объект date.
        
        Args:
            date_str: Строка с датой в различных форматах
            
        Returns:
            datetime.date: Объект даты
        """
        try:
            # Проверяем разные форматы
            formats = [
                "%Y-%m-%d",      # 2023-01-31
                "%d.%m.%Y",      # 31.01.2023
                "%d/%m/%Y",      # 31/01/2023
                "%Y%m%d"         # 20230131
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            
            # Если ни один формат не подошел, пробуем разобрать как timestamp
            try:
                return datetime.fromtimestamp(int(date_str)).date()
            except (ValueError, TypeError):
                pass
            
            # Если все не удалось, возвращаем текущую дату
            logger.warning(f"Не удалось разобрать дату: {date_str}, используем текущую дату")
            return datetime.now().date()
        
        except Exception as e:
            logger.error(f"Ошибка при парсинге даты {date_str}: {str(e)}")
            return datetime.now().date()
    
    async def _parse_time(self, time_str: str) -> datetime.time:
        """
        Парсинг строки времени в объект time.
        
        Args:
            time_str: Строка с временем в различных форматах
            
        Returns:
            datetime.time: Объект времени
        """
        try:
            # Проверяем разные форматы
            formats = [
                "%H:%M:%S",      # 15:30:00
                "%H:%M",         # 15:30
                "%I:%M %p",      # 3:30 PM
                "%I:%M%p",       # 3:30PM
                "%I.%M %p",      # 3.30 PM
                "%H.%M"          # 15.30
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(time_str, fmt).time()
                except ValueError:
                    continue
            
            # Если ни один формат не подошел, пробуем разбить строку
            try:
                # Разбиваем строку по распространенным разделителям
                parts = time_str.replace(".", ":").replace(" ", ":")
                parts = [p for p in parts.split(":") if p]
                
                if len(parts) >= 2:
                    hour = int(parts[0])
                    minute = int(parts[1])
                    second = int(parts[2]) if len(parts) > 2 else 0
                    
                    # Проверяем AM/PM
                    if "pm" in time_str.lower() and hour < 12:
                        hour += 12
                    elif "am" in time_str.lower() and hour == 12:
                        hour = 0
                    
                    return datetime.time(hour, minute, second)
            except (ValueError, IndexError):
                pass
            
            # Если все не удалось, возвращаем текущее время
            logger.warning(f"Не удалось разобрать время: {time_str}, используем текущее время")
            return datetime.now().time()
        
        except Exception as e:
            logger.error(f"Ошибка при парсинге времени {time_str}: {str(e)}")
            return datetime.now().time()
            
    async def get_business_analytics(self) -> Dict[str, Any]:
        """
        Получение расширенной бизнес-аналитики по данным бронирования.
        
        Returns:
            Dict[str, Any]: Словарь с бизнес-аналитикой
        """
        try:
            async with self.pool.acquire() as conn:
                # Диапазоны цен по типу корта
                price_ranges = await conn.fetch(
                    f"""
                    SELECT 
                        court_type,
                        MIN(CAST(REGEXP_REPLACE(price, '[^0-9]', '', 'g') AS INTEGER)) as min_price,
                        MAX(CAST(REGEXP_REPLACE(price, '[^0-9]', '', 'g') AS INTEGER)) as max_price,
                        AVG(CAST(REGEXP_REPLACE(price, '[^0-9]', '', 'g') AS INTEGER)) as avg_price,
                        COUNT(DISTINCT url_id) as venue_count
                    FROM {BOOKING_TABLE}
                    WHERE court_type IS NOT NULL AND price ~ '^[0-9]'
                    GROUP BY court_type
                    ORDER BY avg_price DESC
                    """
                )
                
                # Сравнение цен по категориям времени
                price_comparison = await conn.fetch(
                    f"""
                    SELECT 
                        court_type,
                        time_category,
                        AVG(CAST(REGEXP_REPLACE(price, '[^0-9]', '', 'g') AS INTEGER)) as avg_price,
                        COUNT(*) as slot_count
                    FROM {BOOKING_TABLE}
                    WHERE court_type IS NOT NULL AND time_category IS NOT NULL AND price ~ '^[0-9]'
                    GROUP BY court_type, time_category
                    ORDER BY court_type, 
                        CASE 
                            WHEN time_category = 'DAY' THEN 1 
                            WHEN time_category = 'EVENING' THEN 2 
                            WHEN time_category = 'WEEKEND' THEN 3 
                            ELSE 4 
                        END
                    """
                )
                
                # Доступность по местоположению
                availability = await conn.fetch(
                    f"""
                    SELECT 
                        location_name,
                        date,
                        COUNT(*) as total_slots
                    FROM {BOOKING_TABLE}
                    WHERE location_name IS NOT NULL
                    GROUP BY location_name, date
                    ORDER BY date DESC, location_name
                    LIMIT 100
                    """
                )
                
                # Типы кортов по площадке
                court_types = await conn.fetch(
                    f"""
                    SELECT 
                        u.url,
                        b.location_name,
                        b.court_type,
                        COUNT(*) as slot_count
                    FROM {BOOKING_TABLE} b
                    JOIN {URL_TABLE} u ON b.url_id = u.id
                    WHERE b.court_type IS NOT NULL
                    GROUP BY u.url, b.location_name, b.court_type
                    ORDER BY u.url, b.location_name, slot_count DESC
                    """
                )
                
                # История изменения цен
                price_history = await conn.fetch(
                    """
                    WITH current_prices AS (
                        SELECT 
                            b.id,
                            b.price,
                            b.court_type,
                            b.location_name,
                            b.time_category,
                            u.url
                        FROM booking_data b
                        JOIN urls u ON b.url_id = u.id
                        WHERE b.price IS NOT NULL
                    ),
                    historical_prices AS (
                        SELECT 
                            ph.booking_data_id,
                            ph.price,
                            ph.recorded_at
                        FROM price_history ph
                        WHERE ph.recorded_at >= CURRENT_DATE - INTERVAL '30 days'
                    )
                    SELECT 
                        cp.id,
                        cp.price as current_price,
                        hp.price as historical_price,
                        hp.recorded_at,
                        cp.court_type,
                        cp.location_name,
                        cp.time_category,
                        cp.url
                    FROM current_prices cp
                    JOIN historical_prices hp ON cp.id = hp.booking_data_id
                    WHERE cp.price != hp.price
                    ORDER BY hp.recorded_at DESC
                    LIMIT 100
                    """
                )
                
                # Требование предоплаты по типам кортов
                prepayment_stats = await conn.fetch(
                    f"""
                    SELECT 
                        court_type,
                        prepayment_required,
                        COUNT(*) as count
                    FROM {BOOKING_TABLE}
                    WHERE court_type IS NOT NULL
                    GROUP BY court_type, prepayment_required
                    ORDER BY court_type, prepayment_required
                    """
                )
                
                # Формируем результат
                result = {
                    'price_ranges': [
                        {
                            'court_type': row['court_type'],
                            'min_price': row['min_price'],
                            'max_price': row['max_price'],
                            'avg_price': float(row['avg_price']),
                            'venue_count': row['venue_count']
                        }
                        for row in price_ranges
                    ],
                    'price_comparison': [
                        {
                            'court_type': row['court_type'],
                            'time_category': row['time_category'],
                            'avg_price': float(row['avg_price']),
                            'slot_count': row['slot_count']
                        }
                        for row in price_comparison
                    ],
                    'availability': [
                        {
                            'location_name': row['location_name'],
                            'date': row['date'].isoformat(),
                            'total_slots': row['total_slots']
                        }
                        for row in availability
                    ],
                    'court_types': [
                        {
                            'url': row['url'],
                            'location_name': row['location_name'],
                            'court_type': row['court_type'],
                            'slot_count': row['slot_count']
                        }
                        for row in court_types
                    ],
                    'price_history': [
                        {
                            'id': row['id'],
                            'current_price': row['current_price'],
                            'historical_price': row['historical_price'],
                            'recorded_at': row['recorded_at'].isoformat(),
                            'court_type': row['court_type'],
                            'location_name': row['location_name'],
                            'time_category': row['time_category'],
                            'url': row['url']
                        }
                        for row in price_history
                    ],
                    'prepayment_stats': [
                        {
                            'court_type': row['court_type'],
                            'prepayment_required': row['prepayment_required'],
                            'count': row['count']
                        }
                        for row in prepayment_stats
                    ]
                }
                
                return result
        
        except Exception as e:
            logger.error(f"Ошибка при получении бизнес-аналитики: {str(e)}")
            return {
                'price_ranges': [],
                'price_comparison': [],
                'availability': [],
                'court_types': [],
                'price_history': [],
                'prepayment_stats': []
            }
