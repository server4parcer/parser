"""
Test Enhanced Data Extractor - Unit tests for the enhanced data extraction functionality.
"""
import unittest
import asyncio
from datetime import datetime, time, date
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from playwright.async_api import ElementHandle, Page

from src.parser.data_extractor import EnhancedDataExtractor


class TestEnhancedDataExtractor(unittest.TestCase):
    """Tests for the EnhancedDataExtractor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.extractor = EnhancedDataExtractor()

    def test_initialize(self):
        """Test initialization of extractor."""
        self.assertIsNotNone(self.extractor.time_pattern)
        self.assertIsNotNone(self.extractor.price_pattern)
        self.assertIsNotNone(self.extractor.date_pattern)
        self.assertIsNotNone(self.extractor.seat_pattern)
        self.assertIsNotNone(self.extractor.duration_pattern)
        self.assertIsNotNone(self.extractor.review_pattern)
        self.assertIsNotNone(self.extractor.court_type_patterns)

    def test_parse_date(self):
        """Test date parsing functionality."""
        # Test ISO format
        date_obj = self.extractor.parse_date("2023-01-01")
        self.assertEqual(date_obj, date(2023, 1, 1))

        # Test DD.MM.YYYY format
        date_obj = self.extractor.parse_date("01.01.2023")
        self.assertEqual(date_obj, date(2023, 1, 1))

        # Test DD/MM/YYYY format
        date_obj = self.extractor.parse_date("01/01/2023")
        self.assertEqual(date_obj, date(2023, 1, 1))

        # Test invalid format
        date_obj = self.extractor.parse_date("invalid")
        self.assertIsNone(date_obj)

    def test_parse_time(self):
        """Test time parsing functionality."""
        # Test HH:MM:SS format
        time_obj = self.extractor.parse_time("14:30:00")
        self.assertEqual(time_obj, time(14, 30, 0))

        # Test HH:MM format
        time_obj = self.extractor.parse_time("14:30")
        self.assertEqual(time_obj, time(14, 30, 0))

        # Test AM/PM format
        time_obj = self.extractor.parse_time("2:30 PM")
        self.assertEqual(time_obj, time(14, 30, 0))

        # Test invalid format
        time_obj = self.extractor.parse_time("invalid")
        self.assertIsNone(time_obj)

    def test_determine_time_category(self):
        """Test time category determination."""
        # Test DAY category
        category = self.extractor.determine_time_category("12:00:00", "2023-01-02")
        self.assertEqual(category, "DAY")

        # Test EVENING category
        category = self.extractor.determine_time_category("19:00:00", "2023-01-02")
        self.assertEqual(category, "EVENING")

        # Test WEEKEND category (Monday is 0, so Saturday is 5 and Sunday is 6)
        category = self.extractor.determine_time_category("12:00:00", "2023-01-07")  # Saturday
        self.assertEqual(category, "WEEKEND")

        # Test invalid inputs
        category = self.extractor.determine_time_category("invalid", "2023-01-01")
        self.assertEqual(category, "UNKNOWN")

    def test_extract_seat_number(self):
        """Test seat number extraction."""
        # Test with "Корт 1"
        seat = self.extractor.extract_seat_number("Корт 1")
        self.assertEqual(seat, "1")

        # Test with "Court #2"
        seat = self.extractor.extract_seat_number("Court #2")
        self.assertEqual(seat, "2")

        # Test with "место номер 3"
        seat = self.extractor.extract_seat_number("место номер 3")
        self.assertEqual(seat, "3")

        # Test with no seat number
        seat = self.extractor.extract_seat_number("No seat number here")
        self.assertEqual(seat, "No seat number here")

    def test_clean_price(self):
        """Test price cleaning functionality."""
        # Test with currency symbol
        price = self.extractor.clean_price("1000 ₽")
        self.assertEqual(price, "1000 ₽")

        # Test with text
        price = self.extractor.clean_price("Price: 1500 RUB")
        self.assertEqual(price, "1500 RUB")

        # Test with spaces
        price = self.extractor.clean_price("2 000 руб")
        self.assertEqual(price, "2000 руб")

    @pytest.mark.asyncio
    async def test_extract_location_info(self):
        """Test location info extraction."""
        mock_page = AsyncMock(spec=Page)

        # Mock the selectors and responses
        breadcrumbs = AsyncMock()
        breadcrumbs.text_content = AsyncMock(return_value="Главная > Лунда-Падель-Речной > Бронирование")

        mock_page.query_selector = AsyncMock(side_effect=[breadcrumbs, None, None, None])

        # Call the method
        result = await self.extractor.extract_location_info(mock_page)

        # Verify the result
        self.assertEqual(result["location_name"], "Лунда-Падель-Речной")

    @pytest.mark.asyncio
    async def test_extract_court_type(self):
        """Test court type extraction."""
        mock_element = AsyncMock(spec=ElementHandle)
        mock_element.text_content = AsyncMock(return_value="Ultra Panoramic Court")

        # Call the method
        court_type = await self.extractor.extract_court_type(mock_element)

        # Verify the result
        self.assertEqual(court_type, "Ultra Panoramic")

    @pytest.mark.asyncio
    async def test_extract_duration(self):
        """Test duration extraction."""
        mock_element = AsyncMock(spec=ElementHandle)
        mock_element.text_content = AsyncMock(return_value="Продолжительность: 1.5 часа")

        # Call the method
        duration = await self.extractor.extract_duration(mock_element)

        # Verify the result
        self.assertEqual(duration, 90)  # 1.5 hours = 90 minutes

    @pytest.mark.asyncio
    async def test_extract_review_count(self):
        """Test review count extraction."""
        mock_element = AsyncMock(spec=ElementHandle)
        mock_element.text_content = AsyncMock(return_value="45 отзывов")

        # Call the method
        review_count = await self.extractor.extract_review_count(mock_element)

        # Verify the result
        self.assertEqual(review_count, 45)

    @pytest.mark.asyncio
    async def test_extract_prepayment_required(self):
        """Test prepayment required extraction."""
        mock_element = AsyncMock(spec=ElementHandle)
        mock_element.text_content = AsyncMock(return_value="100% предоплата")

        # Call the method
        prepayment = await self.extractor.extract_prepayment_required(mock_element)

        # Verify the result
        self.assertTrue(prepayment)

        # Test negative case
        mock_element.text_content = AsyncMock(return_value="Оплата на месте")
        prepayment = await self.extractor.extract_prepayment_required(mock_element)
        self.assertFalse(prepayment)