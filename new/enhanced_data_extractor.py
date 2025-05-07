"""
Enhanced Data Extractor - Extract additional data from YCLIENTS pages for business intelligence.
"""
import logging
import re
import json
from datetime import datetime, time, date
from typing import Dict, List, Optional, Any, Tuple, Union

from playwright.async_api import ElementHandle, Page

from src.parser.selectors import SELECTORS, XPATH_SELECTORS


logger = logging.getLogger(__name__)


class EnhancedDataExtractor:
    """
    Enhanced class for extracting and processing data from HTML elements,
    with support for additional business intelligence fields.
    """

    def __init__(self):
        """Initialize the data extractor."""
        # Regular expressions for data extraction
        self.time_pattern = re.compile(r'(\d{1,2})[:\.](\d{2})(?:\s*(AM|PM|am|pm))?')
        self.price_pattern = re.compile(r'(\d+[\.,]?\d*)')
        self.date_pattern = re.compile(r'(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{2,4})|(\d{4})[\/\.-](\d{1,2})[\/\.-](\d{1,2})')
        self.seat_pattern = re.compile(r'(?:место|корт|зал|комната|room|court|seat)\s*(?:[№#]?)?\s*(\d+)', re.IGNORECASE)
        self.duration_pattern = re.compile(r'(\d+)(?:\s*(?:мин|min|час|hour|ч|h))?', re.IGNORECASE)
        self.review_pattern = re.compile(r'(\d+)\s*(?:отзыв|review|оценк|rating)', re.IGNORECASE)
        
        # Court type patterns for precise matching
        self.court_type_patterns = {
            'Ultra Panoramic': [r'ультра\s*панорамик', r'ultra\s*panoramic'],
            'Panoramic': [r'панорамик', r'panoramic'],
            'Single': [r'сингл', r'single', r'одиночный'],
            'PadelTech Full Vision': [r'padeltech\s*full\s*vision', r'падельтех'],
            'WPT Special Edition': [r'wpt\s*special', r'wpt\s*edition'],
            'Standard': [r'стандарт', r'standard', r'обычный']
        }
        
        # Time category thresholds
        self.day_hours = (7, 17)  # 7:00 - 17:00
        self.evening_hours = (17, 23)  # 17:00 - 23:00
        # Weekend is determined by the date, not by time

    async def extract_text_content(self, element: ElementHandle) -> str:
        """
        Extract text content from element.
        
        Args:
            element: HTML element
            
        Returns:
            str: Text content
        """
        try:
            text = await element.text_content()
            return text.strip() if text else ""
        except Exception as e:
            logger.error(f"Error extracting text content: {str(e)}")
            return ""

    async def extract_attribute(self, element: ElementHandle, attr: str) -> str:
        """
        Extract attribute value from element.
        
        Args:
            element: HTML element
            attr: Attribute name
            
        Returns:
            str: Attribute value
        """
        try:
            value = await element.get_attribute(attr)
            return value.strip() if value else ""
        except Exception as e:
            logger.error(f"Error extracting attribute {attr}: {str(e)}")
            return ""

    async def extract_location_info(self, page: Page) -> Dict[str, Any]:
        """
        Extract location information from the page.
        
        Args:
            page: Browser page
            
        Returns:
            Dict[str, Any]: Location information
        """
        try:
            # First try to find location name in breadcrumbs
            breadcrumbs = await page.query_selector('.breadcrumbs, .breadcrumb, .nav-breadcrumb')
            if breadcrumbs:
                breadcrumb_text = await self.extract_text_content(breadcrumbs)
                return self._parse_location_from_text(breadcrumb_text)
            
            # Try to find location in header or title
            header = await page.query_selector('h1, .header, .title, .venue-name')
            if header:
                header_text = await self.extract_text_content(header)
                return self._parse_location_from_text(header_text)
            
            # Look for address information
            address = await page.query_selector('.address, .location, .venue-address')
            if address:
                address_text = await self.extract_text_content(address)
                return self._parse_location_from_text(address_text)
            
            # Try to extract from meta tags
            meta_description = await page.query_selector('meta[name="description"]')
            if meta_description:
                description = await self.extract_attribute(meta_description, 'content')
                return self._parse_location_from_text(description)
            
            # Extract from title as last resort
            title = await page.title()
            return self._parse_location_from_text(title)
        
        except Exception as e:
            logger.error(f"Error extracting location info: {str(e)}")
            return {"location_name": None, "address": None}

    def _parse_location_from_text(self, text: str) -> Dict[str, Any]:
        """
        Parse location information from text.
        
        Args:
            text: Text containing location information
            
        Returns:
            Dict[str, Any]: Location information
        """
        # Known location patterns from the URLs provided
        location_patterns = [
            (r'Лунда[\s-]Падель[\s-]Речной', 'Лунда-Падель-Речной'),
            (r'Лунда[\s-]Падель(?:или)?[\s-](?:\(?)Звезда', 'Лунда-Падель-Звезда'),
            (r'Лунда[\s-]Падель[\s-]Делло[\s-]Спорт', 'Лунда-Падель-Делло-Спорт'),
            (r'Лунда[\s-]Падель[\s-]Сделали[\s-]Сами', 'Лунда-Падель-Сделали-Сами'),
            (r'ТК[\s"]*Ракетлон', 'ТК Ракетлон'),
            (r'Корты[\s-]Сетки', 'Корты-Сетки'),
            (r'Друзья[\s-]по[\s-]паддлу', 'Друзья по паддлу'),
            (r'Педаль[\s-]A33', 'Педаль A33')
        ]
        
        # Look for location patterns
        for pattern, name in location_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # Look for address after the location name
                address_match = re.search(r'(?:[Мм]осква|[Мм]ытищи)[\s,]+([\w\s\.,]+\d+)', text)
                address = address_match.group(0) if address_match else None
                return {"location_name": name, "address": address}
        
        # If no specific pattern is found, try to extract any venue name
        venue_match = re.search(r'["«]([^"»]+)["»]', text)
        if venue_match:
            return {"location_name": venue_match.group(1), "address": None}
        
        # Default return if nothing is found
        return {"location_name": None, "address": None}

    async def extract_court_type(self, element: ElementHandle) -> str:
        """
        Extract court type from element.
        
        Args:
            element: HTML element
            
        Returns:
            str: Court type
        """
        try:
            text = await self.extract_text_content(element)
            
            # Check for known court type patterns
            for court_type, patterns in self.court_type_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        return court_type
            
            # Check for specific court types from the URLs provided
            if re.search(r'ультрапанорамик|ultra\s*panoramic', text, re.IGNORECASE):
                return 'Ultra Panoramic'
            elif re.search(r'панорамик|panoramic', text, re.IGNORECASE):
                return 'Panoramic'
            elif re.search(r'сингл|single|для игры 1 на 1', text, re.IGNORECASE):
                return 'Single'
            elif re.search(r'padeltech|падельтех', text, re.IGNORECASE):
                return 'PadelTech Full Vision'
            elif re.search(r'падельгалис|padelgalis', text, re.IGNORECASE):
                return 'Padelgalis WPT'
            
            # Look for court type by number pattern
            court_match = re.search(r'корт\s*(?:№|#)?\s*(\d+)\s+(.*?)(?:$|\()', text, re.IGNORECASE)
            if court_match:
                type_text = court_match.group(2).strip()
                if type_text:
                    return type_text
            
            # Look for general type description
            type_match = re.search(r'(?:тип|type)\s+(.*?)(?:$|\(|\.|,)', text, re.IGNORECASE)
            if type_match:
                return type_match.group(1).strip()
            
            return "Standard"
        
        except Exception as e:
            logger.error(f"Error extracting court type: {str(e)}")
            return "Standard"

    def determine_time_category(self, time_str: str, date_str: str) -> str:
        """
        Determine time category (DAY, EVENING, WEEKEND) from time and date.
        
        Args:
            time_str: Time string
            date_str: Date string
            
        Returns:
            str: Time category
        """
        try:
            # Parse the time
            time_obj = self.parse_time(time_str)
            if not time_obj:
                return "UNKNOWN"
            
            # Parse the date
            date_obj = self.parse_date(date_str)
            if not date_obj:
                return "UNKNOWN"
            
            # Check if it's a weekend
            if date_obj.weekday() >= 5:  # 5 is Saturday, 6 is Sunday
                return "WEEKEND"
            
            # Check time category
            hour = time_obj.hour
            if self.day_hours[0] <= hour < self.day_hours[1]:
                return "DAY"
            elif self.evening_hours[0] <= hour < self.evening_hours[1]:
                return "EVENING"
            else:
                return "NIGHT"
        
        except Exception as e:
            logger.error(f"Error determining time category for {time_str} on {date_str}: {str(e)}")
            return "UNKNOWN"

    async def extract_duration(self, element: ElementHandle) -> Optional[int]:
        """
        Extract duration from element in minutes.
        
        Args:
            element: HTML element
            
        Returns:
            Optional[int]: Duration in minutes
        """
        try:
            text = await self.extract_text_content(element)
            
            # Check for explicit duration in the text
            duration_match = re.search(r'(\d+)\s*(?:мин|min|минут|minutes)', text, re.IGNORECASE)
            if duration_match:
                return int(duration_match.group(1))
            
            # Check for hours format
            hours_match = re.search(r'(\d+)[.,]?(\d*)\s*(?:час|hour|ч|h)', text, re.IGNORECASE)
            if hours_match:
                hours = int(hours_match.group(1))
                minutes = int(hours_match.group(2)) if hours_match.group(2) else 0
                return hours * 60 + minutes
            
            # Check for duration pattern in specific formats ("Аренда 1 час", "1,5 часа")
            specific_duration = re.search(r'(?:аренда|аренда корта на|продолжительность)\s*(\d+)[.,]?(\d*)\s*(?:час|hour|ч|h)', text, re.IGNORECASE)
            if specific_duration:
                hours = int(specific_duration.group(1))
                minutes = int(specific_duration.group(2)) if specific_duration.group(2) else 0
                return hours * 60 + minutes
            
            # Check for time range format (e.g., "10:00-11:30")
            time_range = re.search(r'(\d{1,2})[:.]\d{2}\s*[-–]\s*(\d{1,2})[:.]\d{2}', text)
            if time_range:
                start_hour = int(time_range.group(1))
                end_hour = int(time_range.group(2))
                duration_hours = end_hour - start_hour
                if duration_hours < 0:  # Handle cases like "23:00-01:00"
                    duration_hours += 24
                return duration_hours * 60
            
            # Default duration for padel courts is usually 1.5 hours
            return 90
        
        except Exception as e:
            logger.error(f"Error extracting duration: {str(e)}")
            return None

    async def extract_review_count(self, element: ElementHandle) -> Optional[int]:
        """
        Extract review count from element.
        
        Args:
            element: HTML element
            
        Returns:
            Optional[int]: Review count
        """
        try:
            text = await self.extract_text_content(element)
            
            # Try to find the review count in the text
            review_match = re.search(r'(\d+)\s*(?:отзыв|review|оценк|rating)', text, re.IGNORECASE)
            if review_match:
                return int(review_match.group(1))
            
            # Just look for numbers followed by the word "отзыв" or similar
            simple_match = re.search(r'(\d+)\s*отзыв', text, re.IGNORECASE)
            if simple_match:
                return int(simple_match.group(1))
            
            return None
        
        except Exception as e:
            logger.error(f"Error extracting review count: {str(e)}")
            return None

    async def extract_prepayment_required(self, element: ElementHandle) -> bool:
        """
        Extract prepayment requirement from element.
        
        Args:
            element: HTML element
            
        Returns:
            bool: True if prepayment is required
        """
        try:
            text = await self.extract_text_content(element)
            
            # Check for prepayment indicators
            prepayment_patterns = [
                r'предоплат',
                r'100%\s*предоплата',
                r'prepayment',
                r'pre-?pay',
                r'оплата\s*вперед',
                r'оплата\s*заранее'
            ]
            
            for pattern in prepayment_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error extracting prepayment requirement: {str(e)}")
            return False

    async def extract_enhanced_booking_data_from_slot(self, slot_element: ElementHandle, page: Page, date_str: str) -> Dict[str, Any]:
        """
        Extract all booking data with enhanced business intelligence fields from slot element.
        
        Args:
            slot_element: Slot element
            page: Browser page for additional context
            date_str: Date string for time category determination
            
        Returns:
            Dict[str, Any]: Enhanced booking data
        """
        try:
            # Get basic booking data
            result = {}

            # Extract time
            time_str = await self.extract_time_from_element(slot_element)
            if time_str:
                result['time'] = time_str

            # Extract price
            price = await self.extract_price_from_element(slot_element)
            if price:
                result['price'] = price

            # Extract provider
            provider = await self.extract_provider_from_element(slot_element)
            if provider:
                result['provider'] = provider

            # Extract seat number
            seat = await self.extract_seat_from_element(slot_element)
            if seat:
                result['seat_number'] = seat
            else:
                result['seat_number'] = "Не указано"
            
            # Extract location info
            location_info = await self.extract_location_info(page)
            if location_info.get("location_name"):
                result['location_name'] = location_info.get("location_name")
            
            # Extract court type
            court_type = await self.extract_court_type(slot_element)
            if court_type:
                result['court_type'] = court_type
            
            # Determine time category
            if time_str and date_str:
                result['time_category'] = self.determine_time_category(time_str, date_str)
            
            # Extract duration
            duration = await self.extract_duration(slot_element)
            if duration:
                result['duration'] = duration
            
            # Extract review count
            review_count = await self.extract_review_count(slot_element)
            if review_count:
                result['review_count'] = review_count
            
            # Extract prepayment requirement
            result['prepayment_required'] = await self.extract_prepayment_required(slot_element)
            
            # Extract raw venue data
            result['raw_venue_data'] = {
                "element_text": await self.extract_text_content(slot_element),
                "element_classes": await self.extract_attribute(slot_element, "class"),
                "element_id": await self.extract_attribute(slot_element, "id"),
                "data_attributes": {}
            }
            
            # Get all data attributes
            for attr in ["data-date", "data-time", "data-price", "data-staff", "data-seat"]:
                value = await self.extract_attribute(slot_element, attr)
                if value:
                    result['raw_venue_data']["data_attributes"][attr] = value
            
            # Add timestamp
            result['extracted_at'] = datetime.now().isoformat()
            
            return result

        except Exception as e:
            logger.error(f"Error extracting enhanced booking data from slot: {str(e)}")
            return {}

    # Include all the original extraction methods from DataExtractor
    
    async def extract_date_from_element(self, element: ElementHandle) -> Optional[str]:
        """Extract date from element."""
        try:
            # Try to get date from attributes
            date_attrs = ['data-date', 'date', 'value']
            for attr in date_attrs:
                date_str = await self.extract_attribute(element, attr)
                if date_str:
                    # Try to parse date from attribute
                    parsed_date = self.parse_date(date_str)
                    if parsed_date:
                        return parsed_date.isoformat()

            # If not from attributes, try from text
            text = await self.extract_text_content(element)
            if text:
                parsed_date = self.parse_date(text)
                if parsed_date:
                    return parsed_date.isoformat()

            return None

        except Exception as e:
            logger.error(f"Error extracting date: {str(e)}")
            return None

    async def extract_time_from_element(self, element: ElementHandle) -> Optional[str]:
        """Extract time from element."""
        try:
            # Try to get time from attributes
            time_attrs = ['data-time', 'time', 'value']
            for attr in time_attrs:
                time_str = await self.extract_attribute(element, attr)
                if time_str:
                    # Try to parse time from attribute
                    parsed_time = self.parse_time(time_str)
                    if parsed_time:
                        return parsed_time.isoformat()

            # If not from attributes, try from text
            text = await self.extract_text_content(element)
            if text:
                parsed_time = self.parse_time(text)
                if parsed_time:
                    return parsed_time.isoformat()

            return None

        except Exception as e:
            logger.error(f"Error extracting time: {str(e)}")
            return None

    async def extract_price_from_element(self, element: ElementHandle) -> Optional[str]:
        """Extract price from element."""
        try:
            # Try to get price from attributes
            price_attrs = ['data-price', 'price', 'value']
            for attr in price_attrs:
                price_str = await self.extract_attribute(element, attr)
                if price_str:
                    return self.clean_price(price_str)

            # If not from attributes, try from text
            text = await self.extract_text_content(element)
            if text:
                return self.clean_price(text)

            # If price is in a child element
            price_element = await element.query_selector(SELECTORS['slot_price'])
            if price_element:
                price_text = await self.extract_text_content(price_element)
                return self.clean_price(price_text)

            return None

        except Exception as e:
            logger.error(f"Error extracting price: {str(e)}")
            return None

    async def extract_provider_from_element(self, element: ElementHandle) -> Optional[str]:
        """Extract provider from element."""
        try:
            # Try to get provider from attributes
            provider_attrs = ['data-provider', 'data-staff', 'provider', 'staff']
            for attr in provider_attrs:
                provider_str = await self.extract_attribute(element, attr)
                if provider_str:
                    return provider_str.strip()

            # If provider is in a child element
            provider_element = await element.query_selector(SELECTORS['slot_provider'])
            if provider_element:
                provider_text = await self.extract_text_content(provider_element)
                return provider_text.strip()

            # If provider is in the element text
            text = await self.extract_text_content(element)
            if text and ":" in text:
                # Assume provider is in format "Name: time"
                provider_part = text.split(":", 1)[0].strip()
                if provider_part and len(provider_part) < 50:  # Reasonable limit
                    return provider_part

            return None

        except Exception as e:
            logger.error(f"Error extracting provider: {str(e)}")
            return None

    async def extract_seat_from_element(self, element: ElementHandle) -> Optional[str]:
        """Extract seat number from element."""
        try:
            # Try to get seat number from attributes
            seat_attrs = ['data-seat', 'data-court', 'data-room', 'seat', 'court', 'room']
            for attr in seat_attrs:
                seat_str = await self.extract_attribute(element, attr)
                if seat_str:
                    return seat_str.strip()

            # If seat number is in a child element
            seat_element = await element.query_selector(SELECTORS['slot_seat'])
            if seat_element:
                seat_text = await self.extract_text_content(seat_element)
                return self.extract_seat_number(seat_text)

            # If seat number is in the element text
            text = await self.extract_text_content(element)
            if text:
                seat_number = self.extract_seat_number(text)
                if seat_number:
                    return seat_number

            return None

        except Exception as e:
            logger.error(f"Error extracting seat number: {str(e)}")
            return None

    def parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string to date object."""
        try:
            # If already in ISO format YYYY-MM-DD
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                return datetime.strptime(date_str, '%Y-%m-%d').date()

            # Format DD.MM.YYYY or DD/MM/YYYY
            match = re.search(r'(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{4})', date_str)
            if match:
                day, month, year = map(int, match.groups())
                return date(year, month, day)

            # Format YYYY/MM/DD or YYYY.MM.DD
            match = re.search(r'(\d{4})[\/\.-](\d{1,2})[\/\.-](\d{1,2})', date_str)
            if match:
                year, month, day = map(int, match.groups())
                return date(year, month, day)

            # Format DD.MM.YY or DD/MM/YY
            match = re.search(r'(\d{1,2})[\/\.-](\d{1,2})[\/\.-](\d{2})', date_str)
            if match:
                day, month, year = map(int, match.groups())
                # Determine century for two-digit year
                if year < 50:
                    year += 2000
                else:
                    year += 1900
                return date(year, month, day)

            # Try as Unix timestamp
            try:
                timestamp = int(date_str)
                return datetime.fromtimestamp(timestamp).date()
            except (ValueError, TypeError):
                pass

            # Try other common formats
            for fmt in ['%Y%m%d', '%d%m%Y', '%m%d%Y']:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue

            return None

        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {str(e)}")
            return None

    def parse_time(self, time_str: str) -> Optional[time]:
        """Parse time string to time object."""
        try:
            # If already in ISO format HH:MM:SS
            if re.match(r'^\d{2}:\d{2}(:\d{2})?$', time_str):
                if len(time_str) == 5:  # HH:MM
                    return datetime.strptime(time_str, '%H:%M').time()
                else:  # HH:MM:SS
                    return datetime.strptime(time_str, '%H:%M:%S').time()

            # Extract hours, minutes and AM/PM
            match = self.time_pattern.search(time_str)
            if match:
                hour, minute, am_pm = match.groups()
                hour = int(hour)
                minute = int(minute)

                # Convert 12-hour format to 24-hour if AM/PM is specified
                if am_pm:
                    if am_pm.lower() == 'pm' and hour < 12:
                        hour += 12
                    elif am_pm.lower() == 'am' and hour == 12:
                        hour = 0

                return time(hour, minute)

            # Try as minutes since start of day
            try:
                minutes = int(time_str)
                hour = minutes // 60
                minute = minutes % 60
                return time(hour, minute)
            except ValueError:
                pass

            return None

        except Exception as e:
            logger.error(f"Error parsing time {time_str}: {str(e)}")
            return None

    def clean_price(self, price_str: str) -> str:
        """Clean price string."""
        try:
            # Remove spaces before extracting numeric value
            price_str_clean = price_str.replace(" ", "")

            # Extract numeric value
            match = self.price_pattern.search(price_str_clean)
            if match:
                price = match.group(1)
                # Find currency
                currency = None
                for c in ['₽', 'руб', 'р.', 'RUB', '$', 'USD', '€', 'EUR']:
                    if c in price_str:
                        currency = c
                        break

                # Format result
                if currency:
                    return f"{price} {currency}"
                else:
                    return price

            # If extraction failed, return cleaned original string
            return price_str.strip()

        except Exception as e:
            logger.error(f"Error cleaning price {price_str}: {str(e)}")
            return price_str.strip()

    def extract_seat_number(self, text: str) -> str:
        """Extract seat number from text."""
        try:
            # Try to extract seat number from text
            match = self.seat_pattern.search(text)
            if match:
                return match.group(1)

            # If text is just a number, return it
            if text.isdigit():
                return text

            # Try to find any number in text
            numbers = re.findall(r'\d+', text)
            if numbers:
                return numbers[0]

            # Return original string if all else fails
            return text.strip()

        except Exception as e:
            logger.error(f"Error extracting seat number from {text}: {str(e)}")
            return text.strip()
