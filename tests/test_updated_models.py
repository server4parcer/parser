"""
Test Updated Models - Unit tests for the updated data models.
"""
import unittest
from datetime import datetime
import json

from src.database.models import Url, BookingData, PriceHistory, AvailabilityAnalytics


class TestUpdatedModels(unittest.TestCase):
    """Tests for the updated data models."""

    def test_url_model(self):
        """Test URL model functionality."""
        # Create a URL model instance
        url = Url(
            id=1,
            url="https://example.com",
            title="Example URL",
            description="Example description",
            created_at=datetime(2023, 1, 1, 0, 0, 0),
            updated_at=datetime(2023, 1, 1, 0, 0, 0),
            is_active=True
        )

        # Test to_dict method
        url_dict = url.to_dict()
        self.assertEqual(url_dict["id"], 1)
        self.assertEqual(url_dict["url"], "https://example.com")
        self.assertEqual(url_dict["title"], "Example URL")
        self.assertEqual(url_dict["description"], "Example description")
        self.assertEqual(url_dict["created_at"], "2023-01-01T00:00:00")
        self.assertEqual(url_dict["updated_at"], "2023-01-01T00:00:00")
        self.assertEqual(url_dict["is_active"], True)

        # Test from_dict method
        url2 = Url.from_dict(url_dict)
        self.assertEqual(url2.id, 1)
        self.assertEqual(url2.url, "https://example.com")
        self.assertEqual(url2.title, "Example URL")
        self.assertEqual(url2.description, "Example description")
        self.assertEqual(url2.created_at, datetime(2023, 1, 1, 0, 0, 0))
        self.assertEqual(url2.updated_at, datetime(2023, 1, 1, 0, 0, 0))
        self.assertEqual(url2.is_active, True)

    def test_booking_data_model(self):
        """Test BookingData model functionality."""
        # Create a BookingData model instance with new fields
        booking = BookingData(
            id=1,
            url_id=1,
            url="https://example.com",
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
            extra_data={"additional": "data"},
            created_at=datetime(2023, 1, 1, 0, 0, 0),
            updated_at=datetime(2023, 1, 1, 0, 0, 0)
        )

        # Test to_dict method
        booking_dict = booking.to_dict()
        self.assertEqual(booking_dict["id"], 1)
        self.assertEqual(booking_dict["url"], "https://example.com")
        self.assertEqual(booking_dict["date"], "2023-01-01")
        self.assertEqual(booking_dict["time"], "12:00:00")
        self.assertEqual(booking_dict["price"], "2000 ₽")
        self.assertEqual(booking_dict["provider"], "Test Provider")
        self.assertEqual(booking_dict["seat_number"], "1")
        self.assertEqual(booking_dict["location_name"], "Test Location")
        self.assertEqual(booking_dict["court_type"], "Ultra Panoramic")
        self.assertEqual(booking_dict["time_category"], "DAY")
        self.assertEqual(booking_dict["duration"], 90)
        self.assertEqual(booking_dict["review_count"], 10)
        self.assertEqual(booking_dict["prepayment_required"], True)
        self.assertEqual(booking_dict["raw_venue_data"], {"key": "value"})
        self.assertEqual(booking_dict["created_at"], "2023-01-01T00:00:00")
        self.assertEqual(booking_dict["updated_at"], "2023-01-01T00:00:00")
        self.assertEqual(booking_dict["additional"], "data")

        # Test from_dict method
        booking2 = BookingData.from_dict(booking_dict)
        self.assertEqual(booking2.id, 1)
        self.assertEqual(booking2.url, "https://example.com")
        self.assertEqual(booking2.date, "2023-01-01")
        self.assertEqual(booking2.time, "12:00:00")
        self.assertEqual(booking2.price, "2000 ₽")
        self.assertEqual(booking2.provider, "Test Provider")
        self.assertEqual(booking2.seat_number, "1")
        self.assertEqual(booking2.location_name, "Test Location")
        self.assertEqual(booking2.court_type, "Ultra Panoramic")
        self.assertEqual(booking2.time_category, "DAY")
        self.assertEqual(booking2.duration, 90)
        self.assertEqual(booking2.review_count, 10)
        self.assertEqual(booking2.prepayment_required, True)
        self.assertEqual(booking2.raw_venue_data, {"key": "value"})
        self.assertEqual(booking2.created_at, datetime(2023, 1, 1, 0, 0, 0))
        self.assertEqual(booking2.updated_at, datetime(2023, 1, 1, 0, 0, 0))
        self.assertEqual(booking2.extra_data["additional"], "data")

    def test_price_history_model(self):
        """Test PriceHistory model functionality."""
        # Create a PriceHistory model instance
        history = PriceHistory(
            id=1,
            booking_data_id=1,
            price="2000 ₽",
            recorded_at=datetime(2023, 1, 1, 0, 0, 0)
        )

        # Test to_dict method
        history_dict = history.to_dict()
        self.assertEqual(history_dict["id"], 1)
        self.assertEqual(history_dict["booking_data_id"], 1)
        self.assertEqual(history_dict["price"], "2000 ₽")
        self.assertEqual(history_dict["recorded_at"], "2023-01-01T00:00:00")

        # Test from_dict method
        history2 = PriceHistory.from_dict(history_dict)
        self.assertEqual(history2.id, 1)
        self.assertEqual(history2.booking_data_id, 1)
        self.assertEqual(history2.price, "2000 ₽")
        self.assertEqual(history2.recorded_at, datetime(2023, 1, 1, 0, 0, 0))

    def test_availability_analytics_model(self):
        """Test AvailabilityAnalytics model functionality."""
        # Create an AvailabilityAnalytics model instance
        analytics = AvailabilityAnalytics(
            id=1,
            url_id=1,
            date="2023-01-01",
            time_slot="morning",
            available_count=5,
            total_slots=10,
            recorded_at=datetime(2023, 1, 1, 0, 0, 0)
        )

        # Test to_dict method
        analytics_dict = analytics.to_dict()
        self.assertEqual(analytics_dict["id"], 1)
        self.assertEqual(analytics_dict["url_id"], 1)
        self.assertEqual(analytics_dict["date"], "2023-01-01")
        self.assertEqual(analytics_dict["time_slot"], "morning")
        self.assertEqual(analytics_dict["available_count"], 5)
        self.assertEqual(analytics_dict["total_slots"], 10)
        self.assertEqual(analytics_dict["recorded_at"], "2023-01-01T00:00:00")

        # Test from_dict method
        analytics2 = AvailabilityAnalytics.from_dict(analytics_dict)
        self.assertEqual(analytics2.id, 1)
        self.assertEqual(analytics2.url_id, 1)
        self.assertEqual(analytics2.date, "2023-01-01")
        self.assertEqual(analytics2.time_slot, "morning")
        self.assertEqual(analytics2.available_count, 5)
        self.assertEqual(analytics2.total_slots, 10)
        self.assertEqual(analytics2.recorded_at, datetime(2023, 1, 1, 0, 0, 0))