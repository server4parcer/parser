"""
Database Models - Enhanced models with additional fields for business intelligence.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any


class Url:
    """Model for URL tracking."""
    
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
        """Convert model to dictionary."""
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
        """Create model from dictionary."""
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
    """Enhanced model for booking data with additional business intelligence fields."""
    
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
        # New fields for enhanced business intelligence
        location_name: str = None,
        court_type: str = None,
        time_category: str = None,  # "DAY", "EVENING", "WEEKEND"
        duration: int = None,  # in minutes
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
        # New fields
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
        """Convert model to dictionary."""
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
        
        # Add extra data
        if self.extra_data:
            for key, value in self.extra_data.items():
                if key not in result:
                    result[key] = value
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BookingData':
        """Create model from dictionary."""
        # Extract standard fields
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
        
        # Add extra data
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
    """Model for tracking price changes over time."""
    
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
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "booking_data_id": self.booking_data_id,
            "price": self.price,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PriceHistory':
        """Create model from dictionary."""
        return cls(
            id=data.get("id"),
            booking_data_id=data.get("booking_data_id"),
            price=data.get("price"),
            recorded_at=datetime.fromisoformat(data["recorded_at"]) if data.get("recorded_at") else None
        )


class AvailabilityAnalytics:
    """Model for tracking availability analytics."""
    
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
        """Convert model to dictionary."""
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
        """Create model from dictionary."""
        return cls(
            id=data.get("id"),
            url_id=data.get("url_id"),
            date=data.get("date"),
            time_slot=data.get("time_slot"),
            available_count=data.get("available_count", 0),
            total_slots=data.get("total_slots", 0),
            recorded_at=datetime.fromisoformat(data["recorded_at"]) if data.get("recorded_at") else None
        )
