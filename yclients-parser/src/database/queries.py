"""
Database Queries - SQL-запросы для парсера YCLIENTS с поддержкой бизнес-аналитики.

Модуль содержит готовые SQL-запросы для работы с базой данных.
"""
from typing import Dict, List, Optional, Any, Tuple

from config.settings import BOOKING_TABLE, URL_TABLE


# Запросы для таблицы URL
class UrlQueries:
    """SQL-запросы для работы с таблицей URL."""
    
    @staticmethod
    def get_all(active_only: bool = False) -> Tuple[str, List[Any]]:
        """
        Запрос для получения всех URL.
        
        Args:
            active_only: Только активные URL
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = f"SELECT * FROM {URL_TABLE}"
        params = []
        
        if active_only:
            query += " WHERE is_active = $1"
            params.append(True)
        
        query += " ORDER BY id"
        
        return query, params
    
    @staticmethod
    def get_by_id(url_id: int) -> Tuple[str, List[Any]]:
        """
        Запрос для получения URL по ID.
        
        Args:
            url_id: ID URL
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = f"SELECT * FROM {URL_TABLE} WHERE id = $1"
        params = [url_id]
        
        return query, params
    
    @staticmethod
    def get_by_url(url: str) -> Tuple[str, List[Any]]:
        """
        Запрос для получения URL по URL.
        
        Args:
            url: URL
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = f"SELECT * FROM {URL_TABLE} WHERE url = $1"
        params = [url]
        
        return query, params
    
    @staticmethod
    def create(url: str, title: Optional[str] = None, description: Optional[str] = None) -> Tuple[str, List[Any]]:
        """
        Запрос для создания URL.
        
        Args:
            url: URL
            title: Заголовок
            description: Описание
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = f"""
            INSERT INTO {URL_TABLE} (url, title, description, is_active)
            VALUES ($1, $2, $3, TRUE)
            RETURNING *
        """
        params = [url, title, description]
        
        return query, params
    
    @staticmethod
    def update(
        url_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[str, List[Any]]:
        """
        Запрос для обновления URL.
        
        Args:
            url_id: ID URL
            title: Заголовок
            description: Описание
            is_active: Активность
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        update_fields = []
        params = []
        
        if title is not None:
            update_fields.append(f"title = ${len(params) + 1}")
            params.append(title)
        
        if description is not None:
            update_fields.append(f"description = ${len(params) + 1}")
            params.append(description)
        
        if is_active is not None:
            update_fields.append(f"is_active = ${len(params) + 1}")
            params.append(is_active)
        
        # Если нет полей для обновления, возвращаем запрос для получения URL
        if not update_fields:
            return UrlQueries.get_by_id(url_id)
        
        # Добавляем обновление поля updated_at
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        query = f"""
            UPDATE {URL_TABLE}
            SET {', '.join(update_fields)}
            WHERE id = ${len(params) + 1}
            RETURNING *
        """
        params.append(url_id)
        
        return query, params
    
    @staticmethod
    def delete(url_id: int) -> Tuple[str, List[Any]]:
        """
        Запрос для удаления URL.
        
        Args:
            url_id: ID URL
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = f"DELETE FROM {URL_TABLE} WHERE id = $1"
        params = [url_id]
        
        return query, params


# Запросы для таблицы данных бронирования
class BookingQueries:
    """SQL-запросы для работы с таблицей данных бронирования."""
    
    @staticmethod
    def get_all(
        url_id: Optional[int] = None,
        url: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        location_name: Optional[str] = None,
        court_type: Optional[str] = None,
        time_category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[str, List[Any]]:
        """
        Запрос для получения всех данных бронирования с новыми фильтрами.
        
        Args:
            url_id: ID URL
            url: URL
            date_from: Начальная дата
            date_to: Конечная дата
            location_name: Название локации
            court_type: Тип корта
            time_category: Категория времени
            limit: Лимит
            offset: Смещение
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
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
        
        # Добавляем фильтры
        if url_id:
            query += f" AND u.id = ${len(params) + 1}"
            params.append(url_id)
        
        if url:
            query += f" AND u.url = ${len(params) + 1}"
            params.append(url)
        
        if date_from:
            query += f" AND b.date >= ${len(params) + 1}"
            params.append(date_from)
        
        if date_to:
            query += f" AND b.date <= ${len(params) + 1}"
            params.append(date_to)
        
        # Новые фильтры
        if location_name:
            query += f" AND b.location_name = ${len(params) + 1}"
            params.append(location_name)
        
        if court_type:
            query += f" AND b.court_type = ${len(params) + 1}"
            params.append(court_type)
        
        if time_category:
            query += f" AND b.time_category = ${len(params) + 1}"
            params.append(time_category)
        
        # Добавляем сортировку, лимит и смещение
        query += f" ORDER BY b.date DESC, b.time DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])
        
        return query, params
    
    @staticmethod
    def count(
        url_id: Optional[int] = None,
        url: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        location_name: Optional[str] = None,
        court_type: Optional[str] = None,
        time_category: Optional[str] = None
    ) -> Tuple[str, List[Any]]:
        """
        Запрос для подсчета данных бронирования с новыми фильтрами.
        
        Args:
            url_id: ID URL
            url: URL
            date_from: Начальная дата
            date_to: Конечная дата
            location_name: Название локации
            court_type: Тип корта
            time_category: Категория времени
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = f"""
            SELECT COUNT(*)
            FROM {BOOKING_TABLE} b
            JOIN {URL_TABLE} u ON b.url_id = u.id
            WHERE 1=1
        """
        params = []
        
        # Добавляем фильтры
        if url_id:
            query += f" AND u.id = ${len(params) + 1}"
            params.append(url_id)
        
        if url:
            query += f" AND u.url = ${len(params) + 1}"
            params.append(url)
        
        if date_from:
            query += f" AND b.date >= ${len(params) + 1}"
            params.append(date_from)
        
        if date_to:
            query += f" AND b.date <= ${len(params) + 1}"
            params.append(date_to)
        
        # Новые фильтры
        if location_name:
            query += f" AND b.location_name = ${len(params) + 1}"
            params.append(location_name)
        
        if court_type:
            query += f" AND b.court_type = ${len(params) + 1}"
            params.append(court_type)
        
        if time_category:
            query += f" AND b.time_category = ${len(params) + 1}"
            params.append(time_category)
        
        return query, params
    
    @staticmethod
    def get_by_id(booking_id: int) -> Tuple[str, List[Any]]:
        """
        Запрос для получения данных бронирования по ID.
        
        Args:
            booking_id: ID бронирования
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = f"""
            SELECT b.id, u.url, b.date, b.time, b.price, b.provider, b.seat_number, 
                   b.location_name, b.court_type, b.time_category, b.duration, 
                   b.review_count, b.prepayment_required, b.raw_venue_data,
                   b.extra_data, b.created_at, b.updated_at
            FROM {BOOKING_TABLE} b
            JOIN {URL_TABLE} u ON b.url_id = u.id
            WHERE b.id = $1
        """
        params = [booking_id]
        
        return query, params
    
    @staticmethod
    def create(
        url_id: int,
        date: str,
        time: str,
        price: Optional[str] = None,
        provider: Optional[str] = None,
        seat_number: Optional[str] = None,
        location_name: Optional[str] = None,
        court_type: Optional[str] = None,
        time_category: Optional[str] = None,
        duration: Optional[int] = None,
        review_count: Optional[int] = None,
        prepayment_required: Optional[bool] = False,
        raw_venue_data: Optional[Dict[str, Any]] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[Any]]:
        """
        Запрос для создания данных бронирования с новыми полями.
        
        Args:
            url_id: ID URL
            date: Дата
            time: Время
            price: Цена
            provider: Провайдер
            seat_number: Номер места
            location_name: Название локации
            court_type: Тип корта
            time_category: Категория времени
            duration: Продолжительность в минутах
            review_count: Количество отзывов
            prepayment_required: Требуется ли предоплата
            raw_venue_data: Сырые данные о площадке
            extra_data: Дополнительные данные
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = f"""
            INSERT INTO {BOOKING_TABLE}
            (url_id, date, time, price, provider, seat_number, location_name, 
             court_type, time_category, duration, review_count, prepayment_required, 
             raw_venue_data, extra_data)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            ON CONFLICT (url_id, date, time, seat_number) DO UPDATE
            SET price = $4, provider = $5, location_name = $7, court_type = $8, 
                time_category = $9, duration = $10, review_count = $11, 
                prepayment_required = $12, raw_venue_data = $13, extra_data = $14,
                updated_at = CURRENT_TIMESTAMP
            RETURNING *
        """
        params = [
            url_id, date, time, price, provider, seat_number, location_name,
            court_type, time_category, duration, review_count, prepayment_required,
            raw_venue_data, extra_data
        ]
        
        return query, params
    
    @staticmethod
    def update(
        booking_id: int,
        price: Optional[str] = None,
        provider: Optional[str] = None,
        seat_number: Optional[str] = None,
        location_name: Optional[str] = None,
        court_type: Optional[str] = None,
        time_category: Optional[str] = None,
        duration: Optional[int] = None,
        review_count: Optional[int] = None,
        prepayment_required: Optional[bool] = None,
        raw_venue_data: Optional[Dict[str, Any]] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[Any]]:
        """
        Запрос для обновления данных бронирования с новыми полями.
        
        Args:
            booking_id: ID бронирования
            price: Цена
            provider: Провайдер
            seat_number: Номер места
            location_name: Название локации
            court_type: Тип корта
            time_category: Категория времени
            duration: Продолжительность в минутах
            review_count: Количество отзывов
            prepayment_required: Требуется ли предоплата
            raw_venue_data: Сырые данные о площадке
            extra_data: Дополнительные данные
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        update_fields = []
        params = []
        
        # Стандартные поля
        if price is not None:
            update_fields.append(f"price = ${len(params) + 1}")
            params.append(price)
        
        if provider is not None:
            update_fields.append(f"provider = ${len(params) + 1}")
            params.append(provider)
        
        if seat_number is not None:
            update_fields.append(f"seat_number = ${len(params) + 1}")
            params.append(seat_number)
        
        # Новые поля
        if location_name is not None:
            update_fields.append(f"location_name = ${len(params) + 1}")
            params.append(location_name)
        
        if court_type is not None:
            update_fields.append(f"court_type = ${len(params) + 1}")
            params.append(court_type)
        
        if time_category is not None:
            update_fields.append(f"time_category = ${len(params) + 1}")
            params.append(time_category)
        
        if duration is not None:
            update_fields.append(f"duration = ${len(params) + 1}")
            params.append(duration)
        
        if review_count is not None:
            update_fields.append(f"review_count = ${len(params) + 1}")
            params.append(review_count)
        
        if prepayment_required is not None:
            update_fields.append(f"prepayment_required = ${len(params) + 1}")
            params.append(prepayment_required)
        
        if raw_venue_data is not None:
            update_fields.append(f"raw_venue_data = ${len(params) + 1}")
            params.append(raw_venue_data)
        
        if extra_data is not None:
            update_fields.append(f"extra_data = ${len(params) + 1}")
            params.append(extra_data)
        
        # Если нет полей для обновления, возвращаем запрос для получения данных бронирования
        if not update_fields:
            return BookingQueries.get_by_id(booking_id)
        
        # Добавляем обновление поля updated_at
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        query = f"""
            UPDATE {BOOKING_TABLE}
            SET {', '.join(update_fields)}
            WHERE id = ${len(params) + 1}
            RETURNING *
        """
        params.append(booking_id)
        
        return query, params
    
    @staticmethod
    def delete(booking_id: int) -> Tuple[str, List[Any]]:
        """
        Запрос для удаления данных бронирования.
        
        Args:
            booking_id: ID бронирования
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = f"DELETE FROM {BOOKING_TABLE} WHERE id = $1"
        params = [booking_id]
        
        return query, params
    
    @staticmethod
    def delete_by_url_id(url_id: int) -> Tuple[str, List[Any]]:
        """
        Запрос для удаления данных бронирования по ID URL.
        
        Args:
            url_id: ID URL
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = f"DELETE FROM {BOOKING_TABLE} WHERE url_id = $1"
        params = [url_id]
        
        return query, params
    
    @staticmethod
    def delete_old_data(days: int) -> Tuple[str, List[Any]]:
        """
        Запрос для удаления устаревших данных.
        
        Args:
            days: Количество дней
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = f"DELETE FROM {BOOKING_TABLE} WHERE date < CURRENT_DATE - $1::interval"
        params = [f"{days} days"]
        
        return query, params
    
    # Новые аналитические запросы
    
    @staticmethod
    def get_price_ranges_by_court_type() -> Tuple[str, List[Any]]:
        """
        Запрос для получения диапазонов цен по типу корта.
        
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = f"""
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
        return query, []
    
    @staticmethod
    def get_price_comparison_by_time_category() -> Tuple[str, List[Any]]:
        """
        Запрос для получения сравнения цен по категориям времени.
        
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = f"""
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
        return query, []
    
    @staticmethod
    def get_availability_by_location() -> Tuple[str, List[Any]]:
        """
        Запрос для получения доступности по местоположению.
        
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = f"""
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
        return query, []
    
    @staticmethod
    def get_court_types_by_venue() -> Tuple[str, List[Any]]:
        """
        Запрос для получения типов кортов по площадке.
        
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = f"""
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
        return query, []


# Запросы для новой таблицы price_history
class PriceHistoryQueries:
    """SQL-запросы для работы с таблицей истории цен."""
    
    @staticmethod
    def create(booking_data_id: int, price: str) -> Tuple[str, List[Any]]:
        """
        Запрос для создания записи истории цен.
        
        Args:
            booking_data_id: ID данных бронирования
            price: Цена
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = """
            INSERT INTO price_history (booking_data_id, price)
            VALUES ($1, $2)
            ON CONFLICT (booking_data_id, recorded_at) DO NOTHING
            RETURNING *
        """
        params = [booking_data_id, price]
        
        return query, params
    
    @staticmethod
    def get_by_booking_data_id(booking_data_id: int) -> Tuple[str, List[Any]]:
        """
        Запрос для получения истории цен по ID данных бронирования.
        
        Args:
            booking_data_id: ID данных бронирования
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = """
            SELECT *
            FROM price_history
            WHERE booking_data_id = $1
            ORDER BY recorded_at DESC
        """
        params = [booking_data_id]
        
        return query, params
    
    @staticmethod
    def get_price_changes(days: int = 30) -> Tuple[str, List[Any]]:
        """
        Запрос для получения изменений цен за указанное количество дней.
        
        Args:
            days: Количество дней
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = f"""
            WITH current_prices AS (
                SELECT 
                    b.id,
                    b.price,
                    b.court_type,
                    b.location_name,
                    b.time_category,
                    u.url
                FROM {BOOKING_TABLE} b
                JOIN {URL_TABLE} u ON b.url_id = u.id
                WHERE b.price IS NOT NULL
            ),
            historical_prices AS (
                SELECT 
                    ph.booking_data_id,
                    ph.price,
                    ph.recorded_at
                FROM price_history ph
                WHERE ph.recorded_at >= CURRENT_DATE - INTERVAL '$1 days'
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
        params = [days]
        
        return query, params


# Запросы для новой таблицы availability_analytics
class AvailabilityAnalyticsQueries:
    """SQL-запросы для работы с таблицей аналитики доступности."""
    
    @staticmethod
    def create(
        url_id: int, 
        date: str, 
        time_slot: str, 
        available_count: int, 
        total_slots: int
    ) -> Tuple[str, List[Any]]:
        """
        Запрос для создания записи аналитики доступности.
        
        Args:
            url_id: ID URL
            date: Дата
            time_slot: Временной слот
            available_count: Количество доступных слотов
            total_slots: Общее количество слотов
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = """
            INSERT INTO availability_analytics 
            (url_id, date, time_slot, available_count, total_slots)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (url_id, date, time_slot, recorded_at) DO UPDATE
            SET available_count = $4, total_slots = $5
            RETURNING *
        """
        params = [url_id, date, time_slot, available_count, total_slots]
        
        return query, params
    
    @staticmethod
    def get_availability_trends(days: int = 30) -> Tuple[str, List[Any]]:
        """
        Запрос для получения трендов доступности за указанное количество дней.
        
        Args:
            days: Количество дней
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = """
            SELECT 
                aa.date,
                aa.time_slot,
                u.url,
                aa.available_count,
                aa.total_slots,
                CASE 
                    WHEN aa.total_slots > 0 THEN 
                        ROUND((aa.available_count::float / aa.total_slots::float) * 100, 2)
                    ELSE 0
                END as availability_percentage,
                aa.recorded_at
            FROM availability_analytics aa
            JOIN urls u ON aa.url_id = u.id
            WHERE aa.date >= CURRENT_DATE - INTERVAL '$1 days'
            ORDER BY aa.date DESC, aa.time_slot
            LIMIT 100
        """
        params = [days]
        
        return query, params