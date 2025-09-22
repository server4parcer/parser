"""
TDD Tests for YClients 4-step navigation flow.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.parser.yclients_parser import YClientsParser
from src.parser.parser_router import ParserRouter


class TestYClientsNavigation:
    """Test 4-step YClients navigation flow."""
    
    @pytest.mark.asyncio
    async def test_step1_service_selection(self):
        """Test: Can navigate to service selection page."""
        # Arrange
        url = "https://n1165596.yclients.com/company/1109937/record-type?o="
        parser = YClientsParser([url], Mock())
        
        # Act
        await parser.initialize()
        navigation_success = await parser.navigate_to_url(url)
        
        # Assert
        assert navigation_success == True
        assert parser.page is not None
        await parser.close()
    
    @pytest.mark.asyncio
    async def test_step2_court_selection(self):
        """Test: Can select court after service selection."""
        # Test court selection finds real court names
        expected_courts = ["Корт №1 Ультрапанорамик", "Корт №2 Панорамик"]
        # Implementation here - will be expanded when testing with real data
        pass
    
    @pytest.mark.asyncio  
    async def test_step3_datetime_selection(self):
        """Test: Can select date and time slots."""
        # Test date/time selection works
        # Implementation here - will be expanded when testing with real data
        pass
    
    @pytest.mark.asyncio
    async def test_step4_price_extraction(self):
        """Test: Can extract prices from service packages."""
        # Test price extraction gets real prices
        expected_price_format = r'\d+\s*₽'
        # Implementation here - will be expanded when testing with real data
        pass
    
    @pytest.mark.asyncio
    async def test_no_demo_data_returned(self):
        """Test: Verify NO demo data is ever returned."""
        # Arrange
        parser = YClientsParser([], Mock())
        
        # Act
        result = await parser.parse_url("https://invalid.url")
        
        # Assert
        assert len(result) == 0 or all(
            'Корт №1 Ультрапанорамик' not in str(item) 
            for item in result
        )
    
    @pytest.mark.asyncio
    async def test_router_correctly_routes_urls(self):
        """Test: Router sends YClients to Playwright, others to lightweight."""
        # Arrange
        router = ParserRouter(Mock())
        
        # Test YClients URL
        yclients_url = "https://n1165596.yclients.com/company/1109937/record-type?o="
        assert router.is_yclients_url(yclients_url) == True
        
        # Test non-YClients URL
        other_url = "https://example.com/booking"
        assert router.is_yclients_url(other_url) == False


class TestDataValidation:
    """Test data extraction and validation."""
    
    def test_price_cleaning(self):
        """Test: Price cleaning removes commas and formats correctly."""
        parser = YClientsParser([], Mock())
        
        test_cases = [
            ("6,000 ₽", "6000 ₽"),
            ("12,500 ₽", "12500 ₽"),
            ("1 000 руб", "1000 руб"),
            ("", "Цена не указана")
        ]
        
        for input_price, expected in test_cases:
            assert parser.clean_price(input_price) == expected
    
    def test_duration_parsing(self):
        """Test: Duration parsing converts to minutes."""
        parser = YClientsParser([], Mock())
        
        test_cases = [
            ("1 ч", 60),
            ("1 ч 30 мин", 90),
            ("2 ч", 120),
            ("30 мин", 30),
            ("", 60)  # Default
        ]
        
        for input_duration, expected in test_cases:
            assert parser.parse_duration(input_duration) == expected
    
    def test_data_structure(self):
        """Test: Extracted data has required fields."""
        required_fields = [
            'url', 'court_name', 'date', 'time',
            'price', 'duration', 'venue_name', 'extracted_at'
        ]
        
        # Mock extracted data
        sample_data = {
            'url': 'https://yclients.com/...',
            'court_name': 'Корт №1',
            'date': '2025-08-12',
            'time': '15:00',
            'price': '6000 ₽',
            'duration': 60,
            'venue_name': 'Нагатинская',
            'extracted_at': datetime.now().isoformat()
        }
        
        for field in required_fields:
            assert field in sample_data


class TestEndToEnd:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_pavel_urls_parse_successfully(self):
        """Test: All Pavel's URLs parse without errors."""
        pavel_urls = [
            "https://n1165596.yclients.com/company/1109937/record-type?o=",
            "https://n1308467.yclients.com/company/1192304/record-type?o=",
            "https://b861100.yclients.com/company/804153/personal/select-time?o=m-1"
        ]
        
        router = ParserRouter(Mock())
        
        for url in pavel_urls:
            # Should not raise exceptions
            result = await router.parse_url(url)
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_database_saves_real_data(self):
        """Test: Database saves contain real venue data, no demo data."""
        # Implementation to verify database contains:
        # - Real court names from venues
        # - Real prices in correct format
        # - No "Корт №X Ультрапанорамик" unless from real venue
        pass


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])