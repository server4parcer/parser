#!/usr/bin/env python3
"""
Export existing data from production Supabase to CSV.
This proves the Supabase connection and data export works.
"""
import os
import sys
import csv

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def export_supabase_to_csv():
    """Export Supabase data to CSV"""

    print("=" * 70)
    print("📊 EXPORT SUPABASE DATA TO CSV")
    print("=" * 70)

    # Check environment
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')

    print(f"Supabase URL: {supabase_url}")
    print(f"Supabase Key: {'***' + supabase_key[-10:] if supabase_key else 'NOT SET'}")
    print("")

    if not supabase_url or not supabase_key:
        print("❌ ERROR: SUPABASE_URL or SUPABASE_KEY not set")
        return False

    try:
        # Import supabase client
        from supabase import create_client

        print("🔌 Connecting to Supabase...")
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Connected")
        print("")

        # Fetch data
        print("📥 Fetching data from booking_data table...")
        response = supabase.table('booking_data') \
            .select('*') \
            .order('id', desc=True) \
            .limit(200) \
            .execute()

        if not response.data:
            print("⚠️  No data found in Supabase")
            print("   Table might be empty or doesn't exist")
            return False

        data = response.data
        print(f"✅ Fetched {len(data)} records")
        print("")

        # Export to CSV
        csv_file = "SUPABASE_EXPORT.csv"
        print(f"💾 Exporting to {csv_file}...")

        # All fields
        if data:
            fieldnames = list(data[0].keys())
        else:
            fieldnames = ['id', 'date', 'time', 'price', 'provider', 'seat_number', 'url']

        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)

        print(f"✅ Exported {len(data)} records to {csv_file}")
        print("")

        # Data quality analysis
        print("=" * 70)
        print("🔍 DATA QUALITY ANALYSIS")
        print("=" * 70)

        has_all_fields = 0
        empty_date = 0
        empty_time = 0
        fake_price = 0
        fake_provider = 0
        duplicates = 0

        seen_keys = set()

        for record in data:
            date = record.get('date')
            time = record.get('time')
            price = record.get('price', '')
            provider = record.get('provider', '')

            # Check all fields present
            if date and time and price and provider:
                has_all_fields += 1

            # Check for missing
            if not date:
                empty_date += 1
            if not time:
                empty_time += 1

            # Check for fake values
            if price == 'Цена не найдена':
                fake_price += 1
            if provider == 'Не указан':
                fake_provider += 1

            # Check duplicates
            key = (date, time, provider)
            if key in seen_keys:
                duplicates += 1
            seen_keys.add(key)

        total = len(data)
        print(f"Total records: {total}")
        print("")
        print("Critical Fields:")
        print(f"   {'✅' if has_all_fields == total else '❌'} All fields present: {has_all_fields}/{total}")
        print(f"   {'✅' if empty_date == 0 else '⚠️ '} Empty dates: {empty_date}")
        print(f"   {'✅' if empty_time == 0 else '⚠️ '} Empty times: {empty_time}")
        print("")
        print("Data Quality:")
        print(f"   {'✅' if fake_price == 0 else '⚠️ '} Fake prices: {fake_price}")
        print(f"   {'✅' if fake_provider == 0 else '⚠️ '} Fake providers: {fake_provider}")
        print(f"   {'✅' if duplicates == 0 else '⚠️ '} Duplicates: {duplicates}")
        print("")

        # Show sample
        print("📋 Sample data (first 5 records):")
        print("-" * 70)
        for i, record in enumerate(data[:5]):
            date = record.get('date', 'NULL')
            time = record.get('time', 'NULL')
            price = record.get('price', 'NULL')
            provider = record.get('provider', 'NULL')
            seat = record.get('seat_number', 'NULL')
            print(f"{i+1}. {date} | {time} | {price} | {provider} | {seat}")
        print("")

        print("=" * 70)
        print(f"✅ SUCCESS! Data exported to {csv_file}")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set environment if not set
    if not os.environ.get('SUPABASE_URL'):
        os.environ['SUPABASE_URL'] = 'https://tfvgbcqjftirclxwqwnr.supabase.co'
    if not os.environ.get('SUPABASE_KEY'):
        os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRmdmdiY3FqZnRpcmNseHdxd25yIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Mjc3Nzk2NywiZXhwIjoyMDY4MzUzOTY3fQ.4szXEDqL7KhQlM3RX89DwiFpIO8LxKRek8-CkTM1-aE'

    success = export_supabase_to_csv()
    sys.exit(0 if success else 1)
