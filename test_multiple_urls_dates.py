#!/usr/bin/env python3
"""
Test multiple URLs with FUTURE dates to find availability.
Smart strategy: Try tomorrow, day after tomorrow, etc.
"""
import asyncio
import sys
import os
import csv
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.database.db_manager import DatabaseManager
from src.parser.yclients_parser import YClientsParser

async def test_multiple_urls():
    """Test all production URLs with future date selection"""

    # Production URLs from TimeWeb
    test_urls = [
        "https://n1165596.yclients.com/company/1109937/record-type?o=",
        "https://n1308467.yclients.com/company/1192304/record-type?o=",
        "https://b861100.yclients.com/company/804153/personal/select-time?o=m-1",
        "https://b1009933.yclients.com/company/936902/personal/select-time?o=",
        "https://b918666.yclients.com/company/855029/personal/menu?o=m-1",
    ]

    print("=" * 80)
    print("🔍 TESTING MULTIPLE URLS WITH FUTURE DATES")
    print("=" * 80)
    print(f"Will test {len(test_urls)} URLs")
    print(f"Strategy: Try future dates (tomorrow, day after, etc.)")
    print("")

    db = DatabaseManager()
    await db.initialize()
    print("✅ Database connected")
    print("")

    all_results = []

    for idx, url in enumerate(test_urls):
        print(f"{'='*80}")
        print(f"🌐 URL {idx+1}/{len(test_urls)}: {url}")
        print(f"{'='*80}")

        try:
            parser = YClientsParser([url], db)
            await parser.initialize()

            print(f"⏳ Parsing (this may take 60-90 seconds)...")
            success, data = await parser.parse_url(url)

            print(f"\n📊 Results:")
            print(f"   Success: {success}")
            print(f"   Records: {len(data)}")

            if data and len(data) > 0:
                print(f"\n✅ FOUND DATA! First 3 records:")
                for i, r in enumerate(data[:3]):
                    date = r.get('date', 'NULL')
                    time = r.get('time', 'NULL')
                    price = r.get('price', 'NULL')
                    provider = r.get('provider', 'NULL')
                    print(f"   {i+1}. {date} {time} | {price} | {provider}")

                all_results.extend(data)

                # Save to Supabase
                print(f"\n💾 Saving to Supabase...")
                await db.save_booking_data(url, data)
                print(f"✅ Saved {len(data)} records")
            else:
                print(f"⚠️  No data found for this URL")
                print(f"   (may have no availability for selected dates)")

            await parser.close()

        except Exception as e:
            print(f"❌ Error testing {url}: {e}")
            import traceback
            traceback.print_exc()

        print("")

    await db.close()

    # Final summary
    print("=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    print(f"Total URLs tested: {len(test_urls)}")
    print(f"Total records found: {len(all_results)}")
    print("")

    if all_results:
        print("🎉 SUCCESS! Found booking data")
        print("")

        # Export to CSV
        csv_file = "MULTI_URL_TEST_RESULTS.csv"
        fieldnames = ['date', 'time', 'price', 'provider', 'seat_number',
                     'duration', 'url', 'service_name', 'available', 'extracted_at']

        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(all_results)

        print(f"📄 Exported to: {csv_file}")
        print("")

        # Data quality check
        has_all_fields = sum(1 for r in all_results if r.get('date') and r.get('time') and r.get('price') and r.get('provider'))
        fake_prices = sum(1 for r in all_results if r.get('price') == 'Цена не найдена')
        fake_providers = sum(1 for r in all_results if r.get('provider') == 'Не указан')

        print("🔍 Quality Analysis:")
        print(f"   All fields present: {has_all_fields}/{len(all_results)}")
        print(f"   Fake prices: {fake_prices}")
        print(f"   Fake providers: {fake_providers}")
        print("")

        if has_all_fields == len(all_results) and fake_prices == 0 and fake_providers == 0:
            print("✅ PERFECT! All records have real data!")
            print("🚀 READY TO DEPLOY!")
        else:
            print("⚠️  Some quality issues detected")
            print("   Review the CSV file for details")

        return True
    else:
        print("⚠️  No data found across all URLs")
        print("   Possible reasons:")
        print("   - All venues have no availability")
        print("   - Parser needs debugging")
        print("   - Try different time or dates")
        return False

if __name__ == "__main__":
    os.environ['SUPABASE_URL'] = 'https://zojouvfuvdgniqbmbegs.supabase.co'
    os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpvam91dmZ1dmRnbmlxYm1iZWdzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDMyNDgzMCwiZXhwIjoyMDc1OTAwODMwfQ.D9tQNYmStQ9EddTnxQL-N1hmmCs9CTIJgRp6qhmSJCc'

    success = asyncio.run(test_multiple_urls())
    sys.exit(0 if success else 1)
