"""
Database Queries - SQL-запросы для парсера YCLIENTS.

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
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[str, List[Any]]:
        """
        Запрос для получения всех данных бронирования.
        
        Args:
            url_id: ID URL
            url: URL
            date_from: Начальная дата
            date_to: Конечная дата
            limit: Лимит
            offset: Смещение
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = f"""
            SELECT b.id, u.url, b.date, b.time, b.price, b.provider, b.seat_number, 
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
        
        # Добавляем сортировку, лимит и смещение
        query += f" ORDER BY b.date DESC, b.time DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])
        
        return query, params
    
    @staticmethod
    def count(
        url_id: Optional[int] = None,
        url: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Tuple[str, List[Any]]:
        """
        Запрос для подсчета данных бронирования.
        
        Args:
            url_id: ID URL
            url: URL
            date_from: Начальная дата
            date_to: Конечная дата
            
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
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[Any]]:
        """
        Запрос для создания данных бронирования.
        
        Args:
            url_id: ID URL
            date: Дата
            time: Время
            price: Цена
            provider: Провайдер
            seat_number: Номер места
            extra_data: Дополнительные данные
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        query = f"""
            INSERT INTO {BOOKING_TABLE}
            (url_id, date, time, price, provider, seat_number, extra_data)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (url_id, date, time, seat_number) DO UPDATE
            SET price = $4, provider = $5, extra_data = $7, updated_at = CURRENT_TIMESTAMP
            RETURNING *
        """
        params = [url_id, date, time, price, provider, seat_number, extra_data]
        
        return query, params
    
    @staticmethod
    def update(
        booking_id: int,
        price: Optional[str] = None,
        provider: Optional[str] = None,
        seat_number: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[Any]]:
        """
        Запрос для обновления данных бронирования.
        
        Args:
            booking_id: ID бронирования
            price: Цена
            provider: Провайдер
            seat_number: Номер места
            extra_data: Дополнительные данные
            
        Returns:
            Tuple[str, List[Any]]: SQL-запрос и параметры
        """
        update_fields = []
        params = []
        
        if price is not None:
            update_fields.append(f"price = ${len(params) + 1}")
            params.append(price)
        
        if provider is not None:
            update_fields.append(f"provider = ${len(params) + 1}")
            params.append(provider)
        
        if seat_number is not None:
            update_fields.append(f"seat_number = ${len(params) + 1}")
            params.append(seat_number)
        
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
