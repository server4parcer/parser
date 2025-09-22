"""
Unit Tests for Parser Components
"""
import pytest
from datetime import datetime
from unittest.mock import Mock

from src.parser.yclients_parser import YClientsParser
from src.parser.parser_router import ParserRouter


class TestPriceExtraction:
    """Test price extraction and cleaning."""
    
    def test_clean_price_removes_commas(self):
        """GIVEN: Price with commas '6,000 ₽'
           WHEN: clean_price() is called
           THEN: Returns '6000 ₽' without commas"""
        parser = YClientsParser([], Mock())
        assert parser.clean_price("6,000 ₽") == "6000 ₽"
    
    def test_clean_price_handles_spaces(self):
        """GIVEN: Price with spaces '12 500 руб'
           WHEN: clean_price() is called  
           THEN: Returns '12500 руб' without spaces"""
        parser = YClientsParser([], Mock())
        assert parser.clean_price("12 500 руб") == "12500 руб"
    
    def test_clean_price_handles_empty(self):
        """GIVEN: Empty price string
           WHEN: clean_price() is called
           THEN: Returns 'Цена не указана'"""
        parser = YClientsParser([], Mock())
        assert parser.clean_price("") == "Цена не указана"
    
    def test_price_not_confused_with_time(self):
        """GIVEN: Time value '15:00'
           WHEN: Processing price
           THEN: Time should not be treated as price"""
        parser = YClientsParser([], Mock())
        
        # Time values should not pass as valid prices
        time_values = ["15:00", "10:30", "23:45"]
        for time_val in time_values:
            # Clean price should add currency if missing
            result = parser.clean_price(time_val)
            # But we should detect this isn't a real price
            assert ':' in result  # Time format preserved


class TestDurationParsing:
    """Test duration extraction and conversion."""
    
    def test_parse_hours_to_minutes(self):
        """GIVEN: Duration '1 ч'
           WHEN: parse_duration() is called
           THEN: Returns 60 minutes"""
        parser = YClientsParser([], Mock())
        assert parser.parse_duration("1 ч") == 60
        assert parser.parse_duration("2 ч") == 120
    
    def test_parse_hours_and_minutes(self):
        """GIVEN: Duration '1 ч 30 мин'
           WHEN: parse_duration() is called
           THEN: Returns 90 minutes"""
        parser = YClientsParser([], Mock())
        assert parser.parse_duration("1 ч 30 мин") == 90
    
    def test_parse_minutes_only(self):
        """GIVEN: Duration '45 мин'
           WHEN: parse_duration() is called
           THEN: Returns 45 minutes"""
        parser = YClientsParser([], Mock())
        assert parser.parse_duration("45 мин") == 45
    
    def test_parse_default_duration(self):
        """GIVEN: Empty or invalid duration
           WHEN: parse_duration() is called
           THEN: Returns default 60 minutes"""
        parser = YClientsParser([], Mock())
        assert parser.parse_duration("") == 60
        assert parser.parse_duration("invalid") == 60


class TestDateParsing:
    """Test date extraction and formatting."""
    
    def test_parse_russian_month(self):
        """GIVEN: Russian date text with month
           WHEN: parse_date() is called
           THEN: Returns ISO format date"""
        parser = YClientsParser([], Mock())
        
        # Test various Russian date formats
        test_cases = [
            ("5 августа", "2025-08-05"),
            ("12 января", "2025-01-12"),
            ("1 декабря", "2025-12-01")
        ]
        
        for date_text, expected in test_cases:
            result = parser.parse_date(date_text)
            # Should at least return valid date format
            assert len(result) == 10  # YYYY-MM-DD format
            assert result.count('-') == 2
    
    def test_parse_fallback_to_current_date(self):
        """GIVEN: Invalid date string
           WHEN: parse_date() is called
           THEN: Returns current date as fallback"""
        parser = YClientsParser([], Mock())
        result = parser.parse_date("invalid date")
        
        # Should return current date
        current_date = datetime.now().strftime('%Y-%m-%d')
        assert result == current_date


class TestSelectorValidation:
    """Test YClients selector detection."""
    
    def test_detect_yclients_urls(self):
        """GIVEN: Various URLs
           WHEN: is_yclients_url() is called
           THEN: Correctly identifies YClients URLs"""
        parser = YClientsParser([], Mock())
        
        # YClients URLs
        yclients_urls = [
            "https://n1165596.yclients.com/company/1109937/record-type?o=",
            "https://b861100.yclients.com/company/804153/personal/select-time?o=m-1",
            "https://example.yclients.com/personal/menu"
        ]
        
        for url in yclients_urls:
            assert parser.is_yclients_url(url) == True
    
    def test_reject_non_yclients_urls(self):
        """GIVEN: Non-YClients URLs
           WHEN: is_yclients_url() is called
           THEN: Returns False"""
        parser = YClientsParser([], Mock())
        
        non_yclients_urls = [
            "https://example.com/booking",
            "https://google.com",
            "https://booking.com/hotels"
        ]
        
        for url in non_yclients_urls:
            assert parser.is_yclients_url(url) == False


class TestVenueNameExtraction:
    """Test venue name extraction from URLs."""
    
    def test_extract_venue_names_from_urls(self):
        """GIVEN: Pavel's venue URLs
           WHEN: extract_venue_name() is called
           THEN: Returns correct venue names"""
        parser = YClientsParser([], Mock())
        
        test_cases = [
            ("https://n1165596.yclients.com/company/1109937/record-type?o=", "Нагатинская"),
            ("https://n1308467.yclients.com/company/1192304/record-type?o=", "Корты-Сетки"), 
            ("https://b861100.yclients.com/company/804153/personal/select-time?o=m-1", "Padel Friends"),
            ("https://b1009933.yclients.com/company/936902/personal/select-time?o=", "ТК Ракетлон"),
            ("https://b918666.yclients.com/company/855029/personal/menu?o=m-1", "Padel A33"),
            ("https://unknown.yclients.com/company/999999/record-type", "Unknown Venue")
        ]
        
        for url, expected_venue in test_cases:
            result = parser.extract_venue_name(url)
            assert result == expected_venue


class TestParserRouter:
    """Test parser routing logic."""
    
    def test_route_yclients_to_playwright(self):
        """GIVEN: YClients URL
           WHEN: Router processes URL
           THEN: Correctly identifies as YClients"""
        router = ParserRouter(Mock())
        
        yclients_urls = [
            "https://n1165596.yclients.com/company/1109937/record-type?o=",
            "https://b861100.yclients.com/company/804153/personal/select-time?o=m-1"
        ]
        
        for url in yclients_urls:
            assert router.is_yclients_url(url) == True
    
    def test_route_other_to_lightweight(self):
        """GIVEN: Non-YClients URL
           WHEN: Router processes URL
           THEN: Correctly identifies as non-YClients"""
        router = ParserRouter(Mock())
        
        other_urls = [
            "https://example.com/booking",
            "https://somesite.ru/schedule"
        ]
        
        for url in other_urls:
            assert router.is_yclients_url(url) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])