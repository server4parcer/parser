#!/usr/bin/env python3
"""
Test wrapper using EXACT production code + CSV export from Supabase.
This proves the deployed code will work identically.

Flow:
1. Use EXACT same code path as main.py (production)
2. Parse real YClients URL
3. Save to production Supabase
4. Export CSV from Supabase
5. Verify data quality (no duplicates, no fake values)
"""
import asyncio
import sys
import os
import csv
from datetime import datetime

# Same path setup as main.py
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import EXACT production code
from src.database.db_manager import DatabaseManager
from src.parser.yclients_parser import YClientsParser

async def test_and_export():
    """Test production code and export CSV from Supabase"""

    # Production test URL
    test_url = "https://n1165596.yclients.com/company/1109937/record-type?o="

    print("=" * 70)
    print("🚀 PRODUCTION CODE TEST + CSV EXPORT")
    print("=" * 70)
    print(f"Test URL: {test_url}")
    print(f"Supabase: {os.environ.get('SUPABASE_URL', 'NOT SET')}")
    print("")

    # STEP 1: Initialize (exact same as main.py)
    print("STEP 1: Initializing production code...")
    db_manager = DatabaseManager()
    await db_manager.initialize()
    print("✅ DatabaseManager initialized")

    parser = YClientsParser([test_url], db_manager)
    await parser.initialize()
    print("✅ Parser initialized")
    print("")

    # STEP 2: Parse (exact same as main.py run_single_iteration)
    print("STEP 2: Parsing YClients page...")
    print("⏳ This takes 30-60 seconds (real browser automation)...")
    print("")

    success, data = await parser.parse_url(test_url)

    print("=" * 70)
    print(f"📊 PARSING RESULTS:")
    print(f"   Success: {success}")
    print(f"   Records extracted: {len(data)}")
    print("")

    if not success or len(data) == 0:
        print("❌ FAILED: No data extracted")
        print("   Possible reasons:")
        print("   - Network timeout")
        print("   - YClients blocked request")
        print("   - No available timeslots")
        await parser.close()
        await db_manager.close()
        return False

    # Show sample
    print("📋 Sample extracted data (first 3 records):")
    print("-" * 70)
    for i, record in enumerate(data[:3]):
        date = record.get('date', 'NULL')
        time = record.get('time', 'NULL')
        price = record.get('price', 'NULL')
        provider = record.get('provider', 'NULL')
        seat = record.get('seat_number', 'NULL')
        print(f"{i+1}. {date} {time} | {price} | {provider} | Seat: {seat}")
    print("")

    # STEP 3: Save to Supabase (exact same as main.py)
    print("STEP 3: Saving to production Supabase...")
    save_success = await db_manager.save_booking_data(test_url, data)

    if not save_success:
        print("❌ FAILED: Could not save to Supabase")
        await parser.close()
        await db_manager.close()
        return False

    print(f"✅ Saved {len(data)} records to production Supabase")
    print("")

    # STEP 4: Fetch back from Supabase to verify
    print("STEP 4: Fetching data from Supabase to verify...")

    try:
        # Query recent records
        response = db_manager.supabase.table('booking_data') \
            .select('*') \
            .order('id', desc=True) \
            .limit(100) \
            .execute()

        if not response.data:
            print("⚠️  WARNING: No data in Supabase")
            await parser.close()
            await db_manager.close()
            return False

        supabase_data = response.data
        print(f"✅ Fetched {len(supabase_data)} records from Supabase")
        print("")

        # STEP 5: Export to CSV
        print("STEP 5: Exporting to CSV...")
        csv_file = "PRODUCTION_CODE_TEST_RESULTS.csv"

        # Critical fields
        fieldnames = ['id', 'date', 'time', 'price', 'provider', 'seat_number',
                     'duration', 'url', 'service_name', 'available',
                     'created_at', 'updated_at']

        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(supabase_data)

        print(f"✅ Exported to: {csv_file}")
        print("")

        # STEP 6: Data quality analysis
        print("=" * 70)
        print("🔍 DATA QUALITY ANALYSIS")
        print("=" * 70)

        total = len(supabase_data)
        has_all_fields = 0
        has_fake_price = 0
        has_fake_provider = 0
        empty_time = 0
        empty_date = 0

        # Track duplicates
        seen_keys = set()
        duplicates = 0

        for record in supabase_data:
            # Check critical fields
            date = record.get('date')
            time = record.get('time')
            price = record.get('price', '')
            provider = record.get('provider', '')

            if date and time and price and provider:
                has_all_fields += 1

            if not date:
                empty_date += 1
            if not time:
                empty_time += 1

            if price == 'Цена не найдена':
                has_fake_price += 1
            if provider == 'Не указан':
                has_fake_provider += 1

            # Check duplicates
            key = (date, time, provider)
            if key in seen_keys:
                duplicates += 1
            seen_keys.add(key)

        # Print results
        print(f"Total records: {total}")
        print("")
        print("Critical Fields:")
        print(f"   {'✅' if has_all_fields == total else '❌'} All fields present: {has_all_fields}/{total}")
        print(f"   {'✅' if empty_date == 0 else '❌'} Missing date: {empty_date}")
        print(f"   {'✅' if empty_time == 0 else '❌'} Missing time: {empty_time}")
        print("")
        print("Data Quality:")
        print(f"   {'✅' if has_fake_price == 0 else '❌'} Fake prices (Цена не найдена): {has_fake_price}")
        print(f"   {'✅' if has_fake_provider == 0 else '❌'} Fake providers (Не указан): {has_fake_provider}")
        print(f"   {'✅' if duplicates == 0 else '❌'} Duplicate records: {duplicates}")
        print("")

        # Final verdict
        all_good = (
            has_all_fields == total and
            empty_date == 0 and
            empty_time == 0 and
            has_fake_price == 0 and
            has_fake_provider == 0 and
            duplicates == 0
        )

        if all_good:
            print("=" * 70)
            print("🎉 SUCCESS! ALL QUALITY CHECKS PASSED!")
            print("=" * 70)
            print("")
            print("✅ Code is working correctly")
            print("✅ Real data captured (not fake fallbacks)")
            print("✅ No duplicates")
            print("✅ All critical fields present")
            print("")
            print(f"📄 CSV file: {csv_file}")
            print("📊 Review the CSV to see actual data")
            print("")
            print("🚀 READY FOR DEPLOYMENT!")
            print("")
        else:
            print("=" * 70)
            print("⚠️  SOME ISSUES DETECTED")
            print("=" * 70)
            print("")
            print("Review the quality metrics above.")
            print(f"Check the CSV file: {csv_file}")
            print("")

    except Exception as e:
        print(f"❌ Error fetching/exporting data: {e}")
        import traceback
        traceback.print_exc()
        await parser.close()
        await db_manager.close()
        return False

    # Cleanup
    await parser.close()
    await db_manager.close()

    return all_good

if __name__ == "__main__":
    # Ensure environment variables set
    if not os.environ.get('SUPABASE_URL'):
        os.environ['SUPABASE_URL'] = 'https://tfvgbcqjftirclxwqwnr.supabase.co'
    if not os.environ.get('SUPABASE_KEY'):
        os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRmdmdiY3FqZnRpcmNseHdxd25yIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Mjc3Nzk2NywiZXhwIjoyMDY4MzUzOTY3fQ.4szXEDqL7KhQlM3RX89DwiFpIO8LxKRek8-CkTM1-aE'

    success = asyncio.run(test_and_export())
    sys.exit(0 if success else 1)
