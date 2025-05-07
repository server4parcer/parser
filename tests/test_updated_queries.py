"""
Test Updated Queries - Unit tests for the updated database queries.
"""
import unittest
from datetime import datetime

from src.database.queries import UrlQueries, BookingQueries, PriceHistoryQueries, AvailabilityAnalyticsQueries


class TestUpdatedQueries(unittest.TestCase):
    """Tests for the updated database queries."""

    def test_url_queries(self):
        """Test URL queries functionality."""
        # Test get_all query
        query, params = UrlQueries.get_all()
        self.assertIn("SELECT * FROM urls", query)

        # Test get_all with active_only
        query, params = UrlQueries.get_all(active_only=True)
        self.assertIn("WHERE is_active = $1", query)
        self.assertEqual(params, [True])

        # Test get_by_id query
        query, params = UrlQueries.get_by_id(1)
        self.assertIn("WHERE id = $1", query)
        self.assertEqual(params, [1])

        # Test create query
        query, params = UrlQueries.create("https://example.com", "Example URL", "Description")
        self.assertIn("INSERT INTO urls", query)
        self.assertIn("VALUES ($1, $2, $3, TRUE)", query)
        self.assertEqual(params, ["https://example.com", "Example URL", "Description"])

        # Test update query
        query, params = UrlQueries.update(1, "New Title", "New Description", False)
        self.assertIn("UPDATE urls", query)
        self.assertIn("SET title = $1, description = $2, is_active = $3", query)
        self.assertEqual(params, ["New Title", "New Description", False, 1])

        # Test delete query
        query, params = UrlQueries.delete(1)
        self.assertIn("DELETE FROM urls WHERE id = $1", query)
        self.assertEqual(params, [1])

    def test_booking_queries(self):
        """Test BookingQueries functionality with new fields."""
        # Test get_all query with new filters
        query, params = BookingQueries.get_all(
            url_id=1,
            url="https://example.com",
            date_from="2023-01-01",
            date_to="2023-01-31",
            location_name="Test Location",
            court_type="Ultra Panoramic",
            time_category="DAY",
            limit=10,
            offset=0
        )

        self.assertIn("SELECT b.id, u.url, b.date, b.time, b.price, b.provider, b.seat_number", query)
        self.assertIn("b.location_name, b.court_type, b.time_category, b.duration", query)
        self.assertIn("b.review_count, b.prepayment_required, b.raw_venue_data", query)
        self.assertIn("WHERE 1=1", query)
        self.assertIn("AND u.id = $1", query)
        self.assertIn("AND u.url = $2", query)
        self.assertIn("AND b.date >= $3", query)
        self.assertIn("AND b.date <= $4", query)
        self.assertIn("AND b.location_name = $5", query)
        self.assertIn("AND b.court_type = $6", query)
        self.assertIn("AND b.time_category = $7", query)

        self.assertEqual(params, [1, "https://example.com", "2023-01-01", "2023-01-31",
                                 "Test Location", "Ultra Panoramic", "DAY", 10, 0])

        # Test create query with new fields
        query, params = BookingQueries.create(
            url_id=1,
            date="2023-01-01",
            time="12:00:00",
            price="2000 ₽",
            provider="Test Provider",
            seat_number="1",
            location_name="Test Location",
            court_type="Ultra Panoramic",
            time_category="DAY",
            duration=90,
            review_count=10,
            prepayment_required=True,
            raw_venue_data={"key": "value"},
            extra_data={"additional": "data"}
        )

        self.assertIn("INSERT INTO booking_data", query)
        self.assertIn("(url_id, date, time, price, provider, seat_number, location_name", query)
        self.assertIn("court_type, time_category, duration, review_count, prepayment_required", query)
        self.assertIn("raw_venue_data, extra_data)", query)
        self.assertIn("VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)", query)

        # Test analytical queries
        query, params = BookingQueries.get_price_ranges_by_court_type()
        self.assertIn("SELECT court_type", query)
        self.assertIn("MIN(CAST(REGEXP_REPLACE(price, '[^0-9]', '', 'g') AS INTEGER)) as min_price", query)
        self.assertIn("MAX(CAST(REGEXP_REPLACE(price, '[^0-9]', '', 'g') AS INTEGER)) as max_price", query)
        self.assertIn("AVG(CAST(REGEXP_REPLACE(price, '[^0-9]', '', 'g') AS INTEGER)) as avg_price", query)
        self.assertIn("GROUP BY court_type", query)

        query, params = BookingQueries.get_price_comparison_by_time_category()
        self.assertIn("SELECT court_type, time_category", query)
        self.assertIn("AVG(CAST(REGEXP_REPLACE(price, '[^0-9]', '', 'g') AS INTEGER)) as avg_price", query)
        self.assertIn("COUNT(*) as slot_count", query)
        self.assertIn("GROUP BY court_type, time_category", query)

    def test_price_history_queries(self):
        """Test PriceHistoryQueries functionality."""
        # Test create query
        query, params = PriceHistoryQueries.create(1, "2000 ₽")
        self.assertIn("INSERT INTO price_history", query)
        self.assertIn("VALUES ($1, $2)", query)
        self.assertEqual(params, [1, "2000 ₽"])

        # Test get_by_booking_data_id query
        query, params = PriceHistoryQueries.get_by_booking_data_id(1)
        self.assertIn("SELECT * FROM price_history", query)
        self.assertIn("WHERE booking_data_id = $1", query)
        self.assertEqual(params, [1])

        # Test get_price_changes query
        query, params = PriceHistoryQueries.get_price_changes(30)
        self.assertIn("WITH current_prices AS", query)
        self.assertIn("historical_prices AS", query)
        self.assertIn("WHERE ph.recorded_at >= CURRENT_DATE - INTERVAL '$1 days'", query)
        self.assertEqual(params, [30])

    def test_availability_analytics_queries(self):
        """Test AvailabilityAnalyticsQueries functionality."""
        # Test create query
        query, params = AvailabilityAnalyticsQueries.create(
            url_id=1,
            date="2023-01-01",
            time_slot="morning",
            available_count=5,
            total_slots=10
        )

        self.assertIn("INSERT INTO availability_analytics", query)
        self.assertIn("(url_id, date, time_slot, available_count, total_slots)", query)
        self.assertIn("VALUES ($1, $2, $3, $4, $5)", query)
        self.assertEqual(params, [1, "2023-01-01", "morning", 5, 10])

        # Test get_availability_trends query
        query, params = AvailabilityAnalyticsQueries.get_availability_trends(30)
        self.assertIn("SELECT aa.date, aa.time_slot, u.url", query)
        self.assertIn("aa.available_count, aa.total_slots", query)
        self.assertIn("WHERE aa.date >= CURRENT_DATE - INTERVAL '$1 days'", query)
        self.assertEqual(params, [30])