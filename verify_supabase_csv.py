#!/usr/bin/env python3
"""
Verify CSV Data Source - Supabase Check
========================================

This script proves that CSV export data comes DIRECTLY from Supabase.

Usage:
    python3 verify_supabase_csv.py

What it does:
    1. Connects to Supabase and queries booking_data table
    2. Exports data to CSV file
    3. Shows you the data with source verification

This proves the entire flow: Supabase → Python → CSV
"""

import asyncio
import csv
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.database.db_manager import DatabaseManager


async def verify_and_export():
    """Query Supabase and export to CSV to prove data source."""

    print("=" * 80)
    print("🔍 SUPABASE → CSV VERIFICATION")
    print("=" * 80)
    print()

    # Step 1: Connect to Supabase
    print("Step 1: Connecting to Supabase...")
    db = DatabaseManager()
    await db.initialize()
    print("✅ Connected to Supabase")
    print(f"   URL: {db.supabase_url}")
    print()

    # Step 2: Query data from Supabase
    print("Step 2: Querying booking_data table...")
    try:
        response = db.supabase.table('booking_data').select('*').order('created_at', desc=True).limit(100).execute()
        records = response.data
        print(f"✅ Retrieved {len(records)} records from Supabase")
        print()
    except Exception as e:
        print(f"❌ Error querying Supabase: {e}")
        await db.close()
        return

    if not records:
        print("⚠️  No data in Supabase yet. Run the parser first:")
        print("   cd yclients-local-fix")
        print("   export SUPABASE_URL='...'")
        print("   export SUPABASE_KEY='...'")
        print("   python3 -m src.main --mode parser")
        await db.close()
        return

    # Step 3: Show sample data
    print("Step 3: Sample data from Supabase:")
    print("-" * 80)
    for i, record in enumerate(records[:3]):
        print(f"Record {i+1}:")
        print(f"  Date:     {record.get('date', 'N/A')}")
        print(f"  Time:     {record.get('time', 'N/A')}")
        print(f"  Provider: {record.get('provider', 'N/A')}")
        print(f"  Price:    {record.get('price', 'N/A')}")
        print(f"  Seat:     {record.get('seat_number', 'N/A')}")
        print()
    print()

    # Step 4: Export to CSV
    csv_filename = f'supabase_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    csv_path = os.path.join(os.path.dirname(__file__), csv_filename)

    print(f"Step 4: Exporting to CSV: {csv_filename}")

    # Get all field names
    if records:
        fieldnames = list(records[0].keys())

        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

        print(f"✅ Exported {len(records)} records to {csv_filename}")
        print()

    # Step 5: Verification summary
    print("=" * 80)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 80)
    print()
    print("What we proved:")
    print(f"  1. ✅ Connected to Supabase ({db.supabase_url})")
    print(f"  2. ✅ Queried booking_data table ({len(records)} records)")
    print(f"  3. ✅ Exported to CSV ({csv_filename})")
    print()
    print("How to verify:")
    print(f"  1. Open {csv_filename} in Excel/Numbers")
    print(f"  2. Check if you see providers like '{records[0].get('provider', 'N/A')}'")
    print(f"  3. Check if you see prices like '{records[0].get('price', 'N/A')}'")
    print()
    print("Alternative verification (Supabase Dashboard):")
    print("  1. Go to https://supabase.com/dashboard")
    print("  2. Open project: zojouvfuvdgniqbmbegs")
    print("  3. Navigate to Table Editor → booking_data")
    print("  4. Compare rows with CSV - they should MATCH!")
    print()
    print(f"CSV file location: {csv_path}")
    print()

    await db.close()


if __name__ == "__main__":
    asyncio.run(verify_and_export())
