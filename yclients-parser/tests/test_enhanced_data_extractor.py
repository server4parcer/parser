import unittest
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Add parent directory to the path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from src.parser.enhanced_data_extractor import EnhancedDataExtractor
from src.parser.data_extractor import DataExtractor


class TestEnhancedDataExtractor(unittest.TestCase):
    """Test cases for the EnhancedDataExtractor class."""

    def setUp(self):
        """Set up the test environment."""
        self.mock_page = MagicMock()
        self.mock_browser_manager = MagicMock()
        self.extractor = EnhancedDataExtractor(self.mock_browser_manager)

    def test_time_category_determination(self):
        """Test time category determination based on hour."""
        # Test DAY category (9:00 - 16:59)
        self.assertEqual(self.extractor.determine_time_category("09:00"), "DAY")
        self.assertEqual(self.extractor.determine_time_category("12:30"), "DAY")
        self.assertEqual(self.extractor.determine_time_category("16:59"), "DAY")
        
        # Test EVENING category (17:00 - 22:59)
        self.assertEqual(self.extractor.determine_time_category("17:00"), "EVENING")
        self.assertEqual(self.extractor.determine_time_category("20:15"), "EVENING")
        self.assertEqual(self.extractor.determine_time_category("22:59"), "EVENING")
        
        # Test NIGHT category (23:00 - 08:59) - should be classified as EVENING
        self.assertEqual(self.extractor.determine_time_category("23:00"), "EVENING")
        self.assertEqual(self.extractor.determine_time_category("01:30"), "EVENING")
        self.assertEqual(self.extractor.determine_time_category("08:59"), "EVENING")
        
        # Test weekend detection - should override time of day
        self.assertEqual(self.extractor.determine_time_category("12:00", is_weekend=True), "WEEKEND")
        self.assertEqual(self.extractor.determine_time_category("20:00", is_weekend=True), "WEEKEND")
        
        # Test invalid formats - should return default "DAY"
        self.assertEqual(self.extractor.determine_time_category("not a time"), "DAY")
        self.assertEqual(self.extractor.determine_time_category(""), "DAY")
        self.assertEqual(self.extractor.determine_time_category(None), "DAY")

    def test_court_type_detection(self):
        """Test court type detection from description."""
        # Tennis court variations
        self.assertEqual(self.extractor.extract_court_type("Теннисный корт №1"), "TENNIS")
        self.assertEqual(self.extractor.extract_court_type("Крытый теннис"), "TENNIS")
        self.assertEqual(self.extractor.extract_court_type("Tennis Court"), "TENNIS")
        
        # Basketball court variations
        self.assertEqual(self.extractor.extract_court_type("Баскетбольная площадка"), "BASKETBALL")
        self.assertEqual(self.extractor.extract_court_type("Игра в баскетбол"), "BASKETBALL")
        self.assertEqual(self.extractor.extract_court_type("Basketball Court A"), "BASKETBALL")
        
        # Squash court variations
        self.assertEqual(self.extractor.extract_court_type("Сквош корт 3"), "SQUASH")
        self.assertEqual(self.extractor.extract_court_type("Squash Room"), "SQUASH")
        
        # Volleyball court variations
        self.assertEqual(self.extractor.extract_court_type("Волейбольная площадка"), "VOLLEYBALL")
        self.assertEqual(self.extractor.extract_court_type("Volleyball Court"), "VOLLEYBALL")
        
        # Football/soccer field variations
        self.assertEqual(self.extractor.extract_court_type("Футбольное поле"), "FOOTBALL")
        self.assertEqual(self.extractor.extract_court_type("Soccer Field A"), "FOOTBALL")
        
        # Badminton court variations
        self.assertEqual(self.extractor.extract_court_type("Бадминтон"), "BADMINTON")
        self.assertEqual(self.extractor.extract_court_type("Badminton Court"), "BADMINTON")
        
        # Unknown court types should return OTHER
        self.assertEqual(self.extractor.extract_court_type("Зал для йоги"), "OTHER")
        self.assertEqual(self.extractor.extract_court_type("Meeting Room"), "OTHER")
        self.assertEqual(self.extractor.extract_court_type(""), "OTHER")
        self.assertEqual(self.extractor.extract_court_type(None), "OTHER")

    def test_duration_extraction(self):
        """Test duration extraction from description."""
        # Test minute formats
        self.assertEqual(self.extractor.extract_duration("30 минут"), 30)
        self.assertEqual(self.extractor.extract_duration("45 мин."), 45)
        self.assertEqual(self.extractor.extract_duration("60 мин"), 60)
        
        # Test hour formats
        self.assertEqual(self.extractor.extract_duration("1 час"), 60)
        self.assertEqual(self.extractor.extract_duration("2 часа"), 120)
        self.assertEqual(self.extractor.extract_duration("1.5 часа"), 90)
        self.assertEqual(self.extractor.extract_duration("1,5 часа"), 90)
        
        # Test time range formats
        self.assertEqual(self.extractor.extract_duration("12:00 - 13:00"), 60)
        self.assertEqual(self.extractor.extract_duration("10:00-11:30"), 90)
        self.assertEqual(self.extractor.extract_duration("14:15 - 15:45"), 90)
        
        # Test English formats
        self.assertEqual(self.extractor.extract_duration("30 minutes"), 30)
        self.assertEqual(self.extractor.extract_duration("1 hour"), 60)
        self.assertEqual(self.extractor.extract_duration("1.5 hours"), 90)
        
        # Test invalid formats - should return default 60
        self.assertEqual(self.extractor.extract_duration("no duration"), 60)
        self.assertEqual(self.extractor.extract_duration(""), 60)
        self.assertEqual(self.extractor.extract_duration(None), 60)

    def test_review_count_extraction(self):
        """Test review count extraction from text."""
        # Test Russian formats
        self.assertEqual(self.extractor.extract_review_count("125 отзывов"), 125)
        self.assertEqual(self.extractor.extract_review_count("отзывов: 42"), 42)
        self.assertEqual(self.extractor.extract_review_count("(18 отзывов)"), 18)
        
        # Test English formats
        self.assertEqual(self.extractor.extract_review_count("63 reviews"), 63)
        self.assertEqual(self.extractor.extract_review_count("reviews: 29"), 29)
        self.assertEqual(self.extractor.extract_review_count("(7 reviews)"), 7)
        
        # Test invalid formats - should return 0
        self.assertEqual(self.extractor.extract_review_count("no reviews"), 0)
        self.assertEqual(self.extractor.extract_review_count(""), 0)
        self.assertEqual(self.extractor.extract_review_count(None), 0)

    def test_prepayment_required_detection(self):
        """Test detection of prepayment requirement."""
        # Test positive indicators
        self.assertTrue(self.extractor.extract_prepayment_required("Требуется предоплата"))
        self.assertTrue(self.extractor.extract_prepayment_required("Prepayment required"))
        self.assertTrue(self.extractor.extract_prepayment_required("100% предоплата"))
        self.assertTrue(self.extractor.extract_prepayment_required("Оплата заранее"))
        
        # Test negative indicators - should return False
        self.assertFalse(self.extractor.extract_prepayment_required("Оплата на месте"))
        self.assertFalse(self.extractor.extract_prepayment_required("Pay at venue"))
        self.assertFalse(self.extractor.extract_prepayment_required(""))
        self.assertFalse(self.extractor.extract_prepayment_required(None))

    def test_location_extraction(self):
        """Test location extraction from venue description."""
        # Test address parsing
        self.assertEqual(
            self.extractor.extract_location_info("ул. Пушкина, д. 10, Москва"), 
            {"address": "ул. Пушкина, д. 10", "city": "Москва", "region": ""}
        )
        
        self.assertEqual(
            self.extractor.extract_location_info("Невский проспект 25, Санкт-Петербург, Ленинградская область"), 
            {"address": "Невский проспект 25", "city": "Санкт-Петербург", "region": "Ленинградская область"}
        )
        
        # Test English addresses
        self.assertEqual(
            self.extractor.extract_location_info("123 Main St, New York, NY"), 
            {"address": "123 Main St", "city": "New York", "region": "NY"}
        )
        
        # Test with location keywords
        self.assertEqual(
            self.extractor.extract_location_info("Адрес: ул. Ленина 15, г. Казань"), 
            {"address": "ул. Ленина 15", "city": "Казань", "region": ""}
        )
        
        # Test internal _parse_location_from_text method
        self.assertEqual(
            self.extractor._parse_location_from_text("Москва, ул. Тверская, д. 1"),
            {"address": "ул. Тверская, д. 1", "city": "Москва", "region": ""}
        )
        
        # Test incomplete address - should handle gracefully
        self.assertEqual(
            self.extractor.extract_location_info("Только название клуба"), 
            {"address": "", "city": "", "region": ""}
        )
        
        # Test None input - should return empty dict structure
        self.assertEqual(
            self.extractor.extract_location_info(None), 
            {"address": "", "city": "", "region": ""}
        )

    @pytest.mark.asyncio
    @patch.object(EnhancedDataExtractor, 'extract_court_type')
    @patch.object(EnhancedDataExtractor, 'determine_time_category')
    @patch.object(EnhancedDataExtractor, 'extract_duration')
    @patch.object(EnhancedDataExtractor, 'extract_location_info')
    @patch.object(EnhancedDataExtractor, 'extract_review_count')
    @patch.object(EnhancedDataExtractor, 'extract_prepayment_required')
    @patch.object(DataExtractor, 'extract_booking_data_from_slot')
    async def test_enhanced_booking_data_extraction(
        self, mock_base_extract, mock_prepayment, mock_reviews, 
        mock_location, mock_duration, mock_time_category, mock_court_type
    ):
        """Test the enhanced booking data extraction with mocked component methods."""
        # Configure mocks
        mock_slot = MagicMock()
        mock_date = "2023-05-01"
        mock_is_weekend = False
        
        # Base extraction mock
        mock_base_extract.return_value = {
            "date": mock_date,
            "time": "14:00",
            "price": "1000",
            "staff": "John Doe",
            "venue_name": "Sports Club",
            "description": "Tennis Court 1",
            "slot_available": True
        }
        
        # Component mocks
        mock_court_type.return_value = "TENNIS"
        mock_time_category.return_value = "DAY"
        mock_duration.return_value = 60
        mock_location.return_value = {"address": "Main St 1", "city": "New York", "region": "NY"}
        mock_reviews.return_value = 42
        mock_prepayment.return_value = True
        
        # Call the method
        result = await self.extractor.extract_enhanced_booking_data_from_slot(
            mock_slot, mock_date, mock_is_weekend
        )
        
        # Verify result
        self.assertEqual(result["date"], mock_date)
        self.assertEqual(result["time"], "14:00")
        self.assertEqual(result["price"], "1000")
        self.assertEqual(result["court_type"], "TENNIS")
        self.assertEqual(result["time_category"], "DAY")
        self.assertEqual(result["duration"], 60)
        self.assertEqual(result["address"], "Main St 1")
        self.assertEqual(result["city"], "New York")
        self.assertEqual(result["region"], "NY")
        self.assertEqual(result["review_count"], 42)
        self.assertTrue(result["prepayment_required"])
        
        # Verify calls
        mock_base_extract.assert_called_once_with(mock_slot, mock_date)
        mock_court_type.assert_called_once_with("Tennis Court 1")
        mock_time_category.assert_called_once_with("14:00", mock_is_weekend)
        mock_duration.assert_called_once_with("Tennis Court 1")
        mock_location.assert_called_once_with("Sports Club")
        mock_reviews.assert_called_once_with("Sports Club")
        mock_prepayment.assert_called_once_with("Tennis Court 1")

if __name__ == '__main__':
    unittest.main()