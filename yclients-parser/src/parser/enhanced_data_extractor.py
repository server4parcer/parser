"""
Enhanced data extractor for YClients Parser with business intelligence features.
Extends the base DataExtractor with additional data extraction capabilities.
"""

import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from src.parser.data_extractor import DataExtractor


class EnhancedDataExtractor(DataExtractor):
    """
    Enhanced data extractor that provides business intelligence capabilities
    such as court type detection, time categorization, and location extraction.
    """

    # Court type patterns for detection
    COURT_TYPE_PATTERNS = {
        "TENNIS": [r"теннис", r"tennis", r"корт"],
        "BASKETBALL": [r"баскетбол", r"basketball", r"баскет"],
        "FOOTBALL": [r"футбол", r"soccer", r"football", r"футзал"],
        "VOLLEYBALL": [r"волейбол", r"volleyball"],
        "SQUASH": [r"сквош", r"squash"],
        "BADMINTON": [r"бадминтон", r"badminton"]
    }

    # Time ranges for categorization
    TIME_RANGES = {
        "DAY": (9, 17),     # 9:00 - 16:59
        "EVENING": (17, 23)  # 17:00 - 22:59
    }

    # Prepayment indicators
    PREPAYMENT_INDICATORS = [
        r"предоплат", r"prepayment", r"оплата заранее", r"депозит",
        r"payment required", r"pay in advance"
    ]

    def determine_time_category(self, time_str: Optional[str], is_weekend: bool = False) -> str:
        """
        Determine the time category based on the time string.
        
        Args:
            time_str (str): Time string in format "HH:MM"
            is_weekend (bool): Whether the date is a weekend
            
        Returns:
            str: Time category (DAY, EVENING, WEEKEND)
        """
        if is_weekend:
            return "WEEKEND"
            
        if not time_str:
            return "DAY"
            
        try:
            # Parse time string
            time_match = re.match(r"(\d{1,2}):(\d{2})", time_str)
            if not time_match:
                return "DAY"
                
            hour = int(time_match.group(1))
            
            # Determine category based on hour
            if self.TIME_RANGES["DAY"][0] <= hour < self.TIME_RANGES["DAY"][1]:
                return "DAY"
            else:
                return "EVENING"
                
        except (ValueError, AttributeError):
            return "DAY"

    def extract_court_type(self, description: Optional[str]) -> str:
        """
        Extract court type from the booking description.
        
        Args:
            description (str): Booking description or venue name
            
        Returns:
            str: Court type (TENNIS, BASKETBALL, etc., or OTHER if unknown)
        """
        if not description:
            return "OTHER"
            
        description = description.lower()
        
        # Check each court type pattern
        for court_type, patterns in self.COURT_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    return court_type
                    
        return "OTHER"

    def extract_duration(self, description: Optional[str]) -> int:
        """
        Extract duration in minutes from description.
        
        Args:
            description (str): Booking description
            
        Returns:
            int: Duration in minutes (default 60 if not found)
        """
        if not description:
            return 60
            
        # Check for minute formats: "30 минут", "45 мин", etc.
        minute_match = re.search(r"(\d+)\s*(?:минут|мин\.?|minutes?)", description, re.IGNORECASE)
        if minute_match:
            return int(minute_match.group(1))
            
        # Check for hour formats: "1 час", "2 часа", "1.5 hour", etc.
        hour_match = re.search(r"(\d+[.,]?\d*)\s*(?:час|часа|часов|hour|hours)", description, re.IGNORECASE)
        if hour_match:
            hours_str = hour_match.group(1).replace(',', '.')
            return int(float(hours_str) * 60)
            
        # Check for time range formats: "12:00 - 13:00", "10:00-11:30", etc.
        time_range_match = re.search(r"(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})", description)
        if time_range_match:
            start_time = datetime.strptime(time_range_match.group(1), "%H:%M")
            end_time = datetime.strptime(time_range_match.group(2), "%H:%M")
            duration_minutes = (end_time - start_time).total_seconds() / 60
            return int(duration_minutes)
            
        # Default to 60 minutes
        return 60

    def extract_review_count(self, venue_description: Optional[str]) -> int:
        """
        Extract review count from venue description.
        
        Args:
            venue_description (str): Venue description or metadata
            
        Returns:
            int: Number of reviews (0 if not found)
        """
        if not venue_description:
            return 0
            
        # Check for review count patterns in Russian and English
        review_match = re.search(r"(\d+)\s*(?:отзыв|отзыва|отзывов|review|reviews)", 
                                venue_description, re.IGNORECASE)
        if review_match:
            return int(review_match.group(1))
            
        # Alternative format: "отзывов: 42", "reviews: 29"
        alt_match = re.search(r"(?:отзыв|отзыва|отзывов|review|reviews)[:\s]+(\d+)", 
                            venue_description, re.IGNORECASE)
        if alt_match:
            return int(alt_match.group(1))
            
        return 0

    def extract_prepayment_required(self, description: Optional[str]) -> bool:
        """
        Check if prepayment is required based on description.
        
        Args:
            description (str): Booking description
            
        Returns:
            bool: True if prepayment is required, False otherwise
        """
        if not description:
            return False
            
        description = description.lower()
        
        # Check for prepayment indicators
        for indicator in self.PREPAYMENT_INDICATORS:
            if re.search(indicator, description, re.IGNORECASE):
                return True
                
        return False

    def _parse_location_from_text(self, text: str) -> Dict[str, str]:
        """
        Parse location information from text.
        
        Args:
            text (str): Text containing location information
            
        Returns:
            Dict[str, str]: Dictionary with address, city, and region
        """
        location_info = {
            "address": "",
            "city": "",
            "region": ""
        }
        
        # Remove location keywords
        cleaned_text = re.sub(r"(?:адрес|address|location|расположение)[:\s]+", "", text, flags=re.IGNORECASE)
        
        # Try to parse city, address, region
        # Format: "City, Address" or "Address, City, Region"
        parts = [p.strip() for p in cleaned_text.split(',')]
        
        if len(parts) >= 3:
            # Format likely: "Address, City, Region"
            location_info["address"] = parts[0]
            location_info["city"] = parts[1]
            location_info["region"] = parts[2]
        elif len(parts) == 2:
            # Format could be "City, Address" or "Address, City"
            # Heuristic: cities are usually shorter than addresses
            if len(parts[0]) < len(parts[1]):
                location_info["city"] = parts[0]
                location_info["address"] = parts[1]
            else:
                location_info["address"] = parts[0]
                location_info["city"] = parts[1]
        elif len(parts) == 1 and parts[0]:
            # Only one part, assume it's an address
            location_info["address"] = parts[0]
            
        return location_info

    def extract_location_info(self, venue_description: Optional[str]) -> Dict[str, str]:
        """
        Extract location information from venue description.
        
        Args:
            venue_description (str): Venue description or metadata
            
        Returns:
            Dict[str, str]: Dictionary with address, city, and region
        """
        if not venue_description:
            return {"address": "", "city": "", "region": ""}
            
        return self._parse_location_from_text(venue_description)

    async def extract_enhanced_booking_data_from_slot(
        self, slot, date: str, is_weekend: bool = False
    ) -> Dict[str, Any]:
        """
        Extract enhanced booking data from a time slot element.
        
        Args:
            slot: Element handle for the time slot
            date (str): Date string for the booking
            is_weekend (bool): Whether the date is a weekend
            
        Returns:
            Dict[str, Any]: Enhanced booking data with additional fields
        """
        # Get base booking data
        booking_data = await super().extract_booking_data_from_slot(slot, date)
        
        # Extract additional information
        venue_name = booking_data.get("venue_name", "")
        description = booking_data.get("description", "")
        time = booking_data.get("time", "")
        
        # Enhance with business intelligence data
        court_type = self.extract_court_type(description)
        time_category = self.determine_time_category(time, is_weekend)
        duration = self.extract_duration(description)
        location_info = self.extract_location_info(venue_name)
        review_count = self.extract_review_count(venue_name)
        prepayment_required = self.extract_prepayment_required(description)
        
        # Add enhanced data to booking data
        enhanced_data = {
            **booking_data,
            "court_type": court_type,
            "time_category": time_category,
            "duration": duration,
            "address": location_info["address"],
            "city": location_info["city"],
            "region": location_info["region"],
            "review_count": review_count,
            "prepayment_required": prepayment_required
        }
        
        return enhanced_data