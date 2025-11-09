#!/usr/bin/env python3
"""
Quick test to verify deduplication logic works correctly.
Tests the parse_api_responses() method with mock data.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_deduplication():
    """Test that duplicate records are filtered out"""

    # Mock captured API data with duplicates
    mock_captured_data = [
        {
            'api_url': 'https://api.yclients.com/search-timeslots',
            'data': {
                'data': [
                    {
                        'attributes': {
                            'datetime': '2025-11-04T14:00:00+03:00',
                            'time': '14:00',
                            'is_bookable': True
                        }
                    },
                    {
                        'attributes': {
                            'datetime': '2025-11-04T14:00:00+03:00',  # DUPLICATE!
                            'time': '14:00',
                            'is_bookable': True
                        }
                    },
                    {
                        'attributes': {
                            'datetime': '2025-11-04T15:00:00+03:00',  # Different time
                            'time': '15:00',
                            'is_bookable': True
                        }
                    }
                ]
            }
        },
        {
            'api_url': 'https://api.yclients.com/search-services',
            'data': {
                'data': [
                    {
                        'attributes': {
                            'price_min': 2800,
                            'price_max': 2800,
                            'service_name': 'Падел корт'
                        }
                    }
                ]
            }
        }
    ]

    print("🧪 Testing deduplication logic...")
    print(f"Input: 3 timeslots (2 duplicates + 1 unique)")

    # Import parser (will fail if syntax errors)
    try:
        from parser.yclients_parser import YClientsParser
        from database.db_manager import DatabaseManager
        print("✅ Parser imports successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

    # Create mock parser instance
    try:
        class MockDB:
            async def initialize(self): pass
            async def close(self): pass

        parser = YClientsParser(['test'], MockDB())
        parser.scraped_providers = [{'id': None, 'name': 'Корт А33'}]

        # Test parse_api_responses
        results = parser.parse_api_responses(mock_captured_data)

        print(f"\nResults: {len(results)} records")

        # Check deduplication worked
        if len(results) == 2:  # Should be 2 unique (14:00 + 15:00)
            print("✅ Deduplication PASSED - 2 unique records (1 duplicate removed)")

            # Check all have required fields
            for i, rec in enumerate(results):
                date = rec.get('date')
                time = rec.get('time')
                provider = rec.get('provider')
                print(f"  Record {i+1}: date={date}, time={time}, provider={provider}")

                if not (date and time):
                    print(f"❌ FAILED - Record {i+1} missing required fields")
                    return False

            print("✅ All records have date + time")
            return True
        else:
            print(f"❌ FAILED - Expected 2 records, got {len(results)}")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dedup()
    sys.exit(0 if success else 1)
