#!/usr/bin/env python3
"""Quick test with first URL from production list"""
import asyncio
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.database.db_manager import DatabaseManager
from src.parser.yclients_parser import YClientsParser

async def quick_test():
    # First URL from timeweb_parse_urls.txt
    test_url = "https://n1308467.yclients.com/company/1192304/record-type?o="

    print(f"Testing: {test_url}")
    print("="*70)

    db = DatabaseManager()
    await db.initialize()

    parser = YClientsParser([test_url], db)
    await parser.initialize()

    print("Parsing (30-60 sec)...")
    success, data = await parser.parse_url(test_url)

    print(f"\nSuccess: {success}")
    print(f"Records: {len(data)}")

    if data:
        print("\nFirst 3 records:")
        for i, r in enumerate(data[:3]):
            print(f"{i+1}. date={r.get('date')} time={r.get('time')} price={r.get('price')} provider={r.get('provider')}")

        # Save to Supabase
        await db.save_booking_data(test_url, data)
        print(f"\n✅ Saved {len(data)} records to Supabase")

    await parser.close()
    await db.close()

    return len(data) > 0

if __name__ == "__main__":
    os.environ['SUPABASE_URL'] = 'https://zojouvfuvdgniqbmbegs.supabase.co'
    os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpvam91dmZ1dmRnbmlxYm1iZWdzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDMyNDgzMCwiZXhwIjoyMDc1OTAwODMwfQ.D9tQNYmStQ9EddTnxQL-N1hmmCs9CTIJgRp6qhmSJCc'

    success = asyncio.run(quick_test())
    sys.exit(0 if success else 1)
