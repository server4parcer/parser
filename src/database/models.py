"""
Database Models - Модели данных для парсера YCLIENTS с поддержкой бизнес-аналитики.
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
    """Расширенная модель данных бронирования с полями для бизнес-аналитики."""
    
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
        # Новые поля для бизнес-аналитики
        location_name: str = None,
        court_type: str = None,
        time_category: str = None,  # "DAY", "EVENING", "WEEKEND"
        duration: int = None,  # в минутах
        review_count: int = None,
        prepayment_required: bool = False,
        raw_venue_data: Dict[str, Any] = None,
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
        # Новые поля
        self.location_name = location_name
        self.court_type = court_type
        self.time_category = time_category
        self.duration = duration
        self.review_count = review_count
        self.prepayment_required = prepayment_required
        self.raw_venue_data = raw_venue_data or {}
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
            "location_name": self.location_name,
            "court_type": self.court_type,
            "time_category": self.time_category,
            "duration": self.duration,
            "review_count": self.review_count,
            "prepayment_required": self.prepayment_required,
            "raw_venue_data": self.raw_venue_data,
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
            location_name=data.get("location_name"),
            court_type=data.get("court_type"),
            time_category=data.get("time_category"),
            duration=data.get("duration"),
            review_count=data.get("review_count"),
            prepayment_required=data.get("prepayment_required", False),
            raw_venue_data=data.get("raw_venue_data", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )
        
        # Добавляем дополнительные данные
        extra_data = {}
        for key, value in data.items():
            if key not in [
                "id", "url_id", "url", "date", "time", "price", "provider",
                "seat_number", "location_name", "court_type", "time_category",
                "duration", "review_count", "prepayment_required", "raw_venue_data",
                "created_at", "updated_at"
            ]:
                extra_data[key] = value
        
        booking_data.extra_data = extra_data
        
        return booking_data


class PriceHistory:
    """Модель для отслеживания изменений цен."""
    
    def __init__(
        self,
        id: int = None,
        booking_data_id: int = None,
        price: str = None,
        recorded_at: datetime = None
    ):
        self.id = id
        self.booking_data_id = booking_data_id
        self.price = price
        self.recorded_at = recorded_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразование модели в словарь.
        
        Returns:
            Dict[str, Any]: Словарь с данными модели
        """
        return {
            "id": self.id,
            "booking_data_id": self.booking_data_id,
            "price": self.price,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PriceHistory':
        """
        Создание модели из словаря.
        
        Args:
            data: Словарь с данными модели
            
        Returns:
            PriceHistory: Модель истории цен
        """
        return cls(
            id=data.get("id"),
            booking_data_id=data.get("booking_data_id"),
            price=data.get("price"),
            recorded_at=datetime.fromisoformat(data["recorded_at"]) if data.get("recorded_at") else None
        )


class AvailabilityAnalytics:
    """Модель для аналитики доступности."""
    
    def __init__(
        self,
        id: int = None,
        url_id: int = None,
        date: str = None,
        time_slot: str = None,  # "morning", "afternoon", "evening"
        available_count: int = 0,
        total_slots: int = 0,
        recorded_at: datetime = None
    ):
        self.id = id
        self.url_id = url_id
        self.date = date
        self.time_slot = time_slot
        self.available_count = available_count
        self.total_slots = total_slots
        self.recorded_at = recorded_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразование модели в словарь.
        
        Returns:
            Dict[str, Any]: Словарь с данными модели
        """
        return {
            "id": self.id,
            "url_id": self.url_id,
            "date": self.date,
            "time_slot": self.time_slot,
            "available_count": self.available_count,
            "total_slots": self.total_slots,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AvailabilityAnalytics':
        """
        Создание модели из словаря.
        
        Args:
            data: Словарь с данными модели
            
        Returns:
            AvailabilityAnalytics: Модель аналитики доступности
        """
        return cls(
            id=data.get("id"),
            url_id=data.get("url_id"),
            date=data.get("date"),
            time_slot=data.get("time_slot"),
            available_count=data.get("available_count", 0),
            total_slots=data.get("total_slots", 0),
            recorded_at=datetime.fromisoformat(data["recorded_at"]) if data.get("recorded_at") else None
        )