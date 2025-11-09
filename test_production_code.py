#!/usr/bin/env python3
"""
Minimal test wrapper using EXACT production code.
Writes to production Supabase to verify code works identically.
"""
import asyncio
import sys
import os

# Same path setup as main.py
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import EXACT production code
from src.database.db_manager import DatabaseManager
from src.parser.yclients_parser import YClientsParser

async def test_production_code():
    """Test using exact production code flow"""

    # SKIP branch selection, go directly to company time selection page
    # From PLAYWRIGHT_EXPLORATION_FINDINGS.md line 36 - after branch click
    # This is where the TIME→COURT→SERVICE flow should start
    test_url = "https://b911781.yclients.com/company/1168982/personal/select-time?o="

    print("🚀 Starting production code test")
    print(f"URL: {test_url}")
    print("=" * 60)

    # EXACT same initialization as main.py
    db_manager = DatabaseManager()
    await db_manager.initialize()
    print("✅ DatabaseManager initialized (connected to production Supabase)")

    parser = YClientsParser([test_url], db_manager)
    await parser.initialize()
    print("✅ Parser initialized")

    # EXACT same parsing logic as main.py run_single_iteration
    print(f"\n🌐 Parsing {test_url}...")
    success, data = await parser.parse_url(test_url)

    print(f"\n📊 Results:")
    print(f"   Success: {success}")
    print(f"   Records: {len(data)}")

    if data:
        print(f"\n📋 Sample (first 3):")
        for i, record in enumerate(data[:3]):
            print(f"{i+1}. date={record.get('date')} time={record.get('time')} price={record.get('price')} provider={record.get('provider')}")

        # EXACT same save logic as main.py
        print(f"\n💾 Saving to production Supabase...")
        save_success = await db_manager.save_booking_data(test_url, data)

        if save_success:
            print(f"✅ Saved {len(data)} records to production Supabase")
        else:
            print(f"❌ Failed to save to Supabase")
    else:
        print("⚠️  No data extracted")

    # Cleanup
    await parser.close()
    await db_manager.close()
    print("\n✅ Test complete")

    return success and len(data) > 0

if __name__ == "__main__":
    success = asyncio.run(test_production_code())
    sys.exit(0 if success else 1)
