"""
Test Business Intelligence - Unit tests for the business intelligence module.
"""
import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

import pytest
import pandas as pd
import matplotlib.pyplot as plt

from src.business_intelligence_module import BusinessIntelligence


class TestBusinessIntelligence(unittest.TestCase):
    """Tests for the BusinessIntelligence class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock database manager
        self.db_manager = MagicMock()
        self.db_manager.pool = MagicMock()
        self.db_manager.queries = MagicMock()
        self.db_manager.export_path = tempfile.mkdtemp()

        # Create BI instance
        self.bi = BusinessIntelligence(self.db_manager)

    def tearDown(self):
        """Clean up after tests."""
        # Clean up temporary directory
        if hasattr(self, 'db_manager') and hasattr(self.db_manager, 'export_path'):
            if os.path.exists(self.db_manager.export_path):
                for file in os.listdir(self.db_manager.export_path):
                    os.unlink(os.path.join(self.db_manager.export_path, file))
                os.rmdir(self.db_manager.export_path)

    @pytest.mark.asyncio
    async def test_generate_price_comparison_report(self):
        """Test price comparison report generation."""
        # Mock database query results
        mock_conn = AsyncMock()
        mock_rows = [
            {"court_type": "Ultra Panoramic", "min_price": 3000, "avg_price": 4000, "max_price": 5000, "venue_count": 3},
            {"court_type": "Panoramic", "min_price": 2000, "avg_price": 3000, "max_price": 4000, "venue_count": 5},
            {"court_type": "Standard", "min_price": 1500, "avg_price": 2500, "max_price": 3500, "venue_count": 8}
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_rows)

        self.db_manager.pool.acquire = AsyncMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock()
        ))

        # Mock queries
        query_mock = ("SELECT court_type, MIN(price) as min_price...", [])
        self.db_manager.queries.BookingQueries.get_price_ranges_by_court_type = MagicMock(return_value=query_mock)

        # Call the method
        with patch('matplotlib.pyplot.savefig'):  # Mock the savefig method
            report_path = await self.bi.generate_price_comparison_report()

        # Verify the result
        self.assertIsNotNone(report_path)
        self.assertTrue(os.path.exists(report_path))

    @pytest.mark.asyncio
    async def test_generate_time_category_price_report(self):
        """Test time category price report generation."""
        # Mock database query results
        mock_conn = AsyncMock()
        mock_rows = [
            {"court_type": "Ultra Panoramic", "time_category": "DAY", "avg_price": 3000, "slot_count": 10},
            {"court_type": "Ultra Panoramic", "time_category": "EVENING", "avg_price": 4000, "slot_count": 15},
            {"court_type": "Ultra Panoramic", "time_category": "WEEKEND", "avg_price": 5000, "slot_count": 20},
            {"court_type": "Panoramic", "time_category": "DAY", "avg_price": 2000, "slot_count": 12},
            {"court_type": "Panoramic", "time_category": "EVENING", "avg_price": 3000, "slot_count": 18},
            {"court_type": "Panoramic", "time_category": "WEEKEND", "avg_price": 4000, "slot_count": 25}
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_rows)

        self.db_manager.pool.acquire = AsyncMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock()
        ))

        # Mock queries
        query_mock = ("SELECT court_type, time_category, AVG(price) as avg_price...", [])
        self.db_manager.queries.BookingQueries.get_price_comparison_by_time_category = MagicMock(return_value=query_mock)

        # Call the method
        with patch('matplotlib.pyplot.savefig'):  # Mock the savefig method
            report_path = await self.bi.generate_time_category_price_report()

        # Verify the result
        self.assertIsNotNone(report_path)
        self.assertTrue(os.path.exists(report_path))

    @pytest.mark.asyncio
    async def test_generate_availability_heatmap(self):
        """Test availability heatmap generation."""
        # Mock database query results
        mock_conn = AsyncMock()
        mock_rows = [
            {"location_name": "Лунда-Падель-Речной", "date": "2023-01-01", "total_slots": 15},
            {"location_name": "Лунда-Падель-Речной", "date": "2023-01-02", "total_slots": 20},
            {"location_name": "Лунда-Падель-Звезда", "date": "2023-01-01", "total_slots": 10},
            {"location_name": "Лунда-Падель-Звезда", "date": "2023-01-02", "total_slots": 12}
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_rows)

        self.db_manager.pool.acquire = AsyncMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock()
        ))

        # Mock queries
        query_mock = ("SELECT location_name, date, COUNT(*) as total_slots...", [])
        self.db_manager.queries.BookingQueries.get_availability_by_location = MagicMock(return_value=query_mock)

        # Call the method
        with patch('matplotlib.pyplot.savefig'):  # Mock the savefig method
            report_path = await self.bi.generate_availability_heatmap()

        # Verify the result
        self.assertIsNotNone(report_path)
        self.assertTrue(os.path.exists(report_path))

    @pytest.mark.asyncio
    async def test_detect_price_changes(self):
        """Test price change detection report generation."""
        # Mock database query results
        mock_conn = AsyncMock()
        mock_rows = [
            {"id": 1, "current_price": "4000", "historical_price": "3500", "recorded_at": datetime(2023, 1, 1),
             "court_type": "Ultra Panoramic", "location_name": "Лунда-Падель-Речной", "time_category": "WEEKEND", "url": "https://example.com"},
            {"id": 2, "current_price": "3000", "historical_price": "3200", "recorded_at": datetime(2023, 1, 1),
             "court_type": "Panoramic", "location_name": "Лунда-Падель-Звезда", "time_category": "DAY", "url": "https://example2.com"}
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_rows)

        self.db_manager.pool.acquire = AsyncMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock()
        ))

        # Mock queries
        query_mock = ("WITH current_prices AS (SELECT...)...", [30])
        self.db_manager.queries.PriceHistoryQueries.get_price_changes = MagicMock(return_value=query_mock)

        # Call the method
        with patch('matplotlib.pyplot.savefig'):  # Mock the savefig method
            report_path = await self.bi.detect_price_changes()

        # Verify the result
        self.assertIsNotNone(report_path)
        self.assertTrue(os.path.exists(report_path))

    @pytest.mark.asyncio
    async def test_detect_price_changes_no_changes(self):
        """Test price change detection with no changes found."""
        # Mock database query results
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])  # Empty result

        self.db_manager.pool.acquire = AsyncMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock()
        ))

        # Mock queries
        query_mock = ("WITH current_prices AS (SELECT...)...", [30])
        self.db_manager.queries.PriceHistoryQueries.get_price_changes = MagicMock(return_value=query_mock)

        # Call the method
        report_path = await self.bi.detect_price_changes()

        # Verify the result
        self.assertIsNotNone(report_path)
        self.assertTrue(os.path.exists(report_path))

        # Verify that a "no changes" report was created
        html_path = os.path.join(report_path, "price_changes_report.html")
        self.assertTrue(os.path.exists(html_path))

        # Check the content of the HTML file
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("No price changes were detected", content)