"""
Database Models - Модели данных для парсера YCLIENTS.

Модуль содержит модели данных для работы с базой данных.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any


class Url:
    """Модель URL для парсинга."""
    
    def __init__(
        self,
        id: int = None,
        url: str = "",
        title: str = None,
        description: str = None,
        created_at: datetime = None,
        updated_at: datetime = None,
        is_active: bool = True
    ):
        self.id = id
        self.url = url
        self.title = title
        self.description = description
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.is_active = is_active
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразование модели в словарь.
        
        Returns:
            Dict[str, Any]: Словарь с данными модели
        """
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Url':
        """
        Создание модели из словаря.
        
        Args:
            data: Словарь с данными модели
            
        Returns:
            Url: Модель URL
        """
        return cls(
            id=data.get("id"),
            url=data.get("url", ""),
            title=data.get("title"),
            description=data.get("description"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            is_active=data.get("is_active", True)
        )


class BookingData:
    """Модель данных бронирования."""
    
    def __init__(
        self,
        id: int = None,
        url_id: int = None,
        url: str = None,
        date: str = "",
        time: str = "",
        price: str = None,
        provider: str = None,
        seat_number: str = None,
        extra_data: Dict[str, Any] = None,
        created_at: datetime = None,
        updated_at: datetime = None
    ):
        self.id = id
        self.url_id = url_id
        self.url = url
        self.date = date
        self.time = time
        self.price = price
        self.provider = provider
        self.seat_number = seat_number
        self.extra_data = extra_data or {}
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразование модели в словарь.
        
        Returns:
            Dict[str, Any]: Словарь с данными модели
        """
        result = {
            "id": self.id,
            "url_id": self.url_id,
            "url": self.url,
            "date": self.date,
            "time": self.time,
            "price": self.price,
            "provider": self.provider,
            "seat_number": self.seat_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        # Добавляем дополнительные данные
        if self.extra_data:
            for key, value in self.extra_data.items():
                if key not in result:
                    result[key] = value
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BookingData':
        """
        Создание модели из словаря.
        
        Args:
            data: Словарь с данными модели
            
        Returns:
            BookingData: Модель данных бронирования
        """
        # Извлекаем стандартные поля
        booking_data = cls(
            id=data.get("id"),
            url_id=data.get("url_id"),
            url=data.get("url"),
            date=data.get("date", ""),
            time=data.get("time", ""),
            price=data.get("price"),
            provider=data.get("provider"),
            seat_number=data.get("seat_number"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )
        
        # Добавляем дополнительные данные
        extra_data = {}
        for key, value in data.items():
            if key not in [
                "id", "url_id", "url", "date", "time", "price", "provider",
                "seat_number", "created_at", "updated_at"
            ]:
                extra_data[key] = value
        
        booking_data.extra_data = extra_data
        
        return booking_data
