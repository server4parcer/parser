#!/usr/bin/env python3
"""
Quick test to verify provider field is being captured correctly.
This will run the parser locally and show what data gets captured.
"""
import asyncio
import sys
import os

# Add project to path
sys.path.insert(0, '/Users/m/git/clients/yclents/yclients-local-fix')

from src.database.db_manager import DatabaseManager
from src.parser.yclients_parser import YClientsParser

async def test_provider_capture():
    """Test if provider field is captured correctly"""
    
    print("="*80)
    print("TESTING PROVIDER FIELD CAPTURE - LOCAL RUN")
    print("="*80)
    print()
    
    # Initialize database
    print("1. Initializing database connection...")
    db = DatabaseManager()
    await db.initialize()
    print("   ✅ Database connected\n")
    
    # Test URL
    url = 'https://b861100.yclients.com/company/804153/personal/select-time?o=m-1'
    print(f"2. Testing URL: {url}")
    print()
    
    # Initialize parser
    print("3. Initializing parser...")
    parser = YClientsParser([url], db)
    await parser.initialize()
    print("   ✅ Parser initialized\n")
    
    # Parse URL
    print("4. Running parser (this may take 30-60 seconds)...")
    print("   [Navigating to page, clicking buttons, scraping data...]")
    print()
    
    success, data = await parser.parse_url(url)
    
    # Close parser
    await parser.close()
    
    # Analyze results
    print("="*80)
    print("RESULTS")
    print("="*80)
    print()
    
    if not success:
        print("❌ FAILED: Parser returned success=False")
        print("   No data was extracted")
        await db.close()
        sys.exit(1)
    
    if not data:
        print("❌ FAILED: No data returned")
        await db.close()
        sys.exit(1)
    
    print(f"✅ SUCCESS: Extracted {len(data)} records")
    print()
    
    # Show first 3 records
    print("First 3 records:")
    print("-" * 80)
    
    provider_found = False
    
    for i, record in enumerate(data[:3], 1):
        print(f"\nRecord {i}:")
        print(f"  Date:     {record.get('date')}")
        print(f"  Time:     {record.get('time')}")
        print(f"  Price:    {record.get('price')}")
        print(f"  Provider: {record.get('provider')}")  # ← KEY FIELD
        print(f"  Service:  {record.get('service_name', 'N/A')}")
        
        # Check if provider is captured
        provider = record.get('provider', '')
        if provider and provider != 'Unknown' and 'Корт' in provider:
            provider_found = True
    
    print()
    print("="*80)
    print("VALIDATION")
    print("="*80)
    print()
    
    # Validate
    first_record = data[0]
    provider = first_record.get('provider', '')
    
    if provider == 'Unknown':
        print("❌ TEST FAILED!")
        print(f"   Provider is still 'Unknown'")
        print(f"   Expected: 'Корт 3 (для игры 1х1)' or similar")
        print()
        print("   This means the selector fix didn't work.")
        print("   Check the selector in src/parser/yclients_parser.py line 1056")
        await db.close()
        sys.exit(1)
    
    elif 'Корт' in provider:
        print("✅ TEST PASSED!")
        print(f"   Provider captured correctly: '{provider}'")
        print(f"   Price captured: {first_record.get('price')}")
        print()
        print("   The fix is working! Ready to deploy to TimeWeb.")
        
        # Save to Supabase
        print()
        print("5. Saving to Supabase...")
        try:
            await db.save_booking_data(url, data)
            print(f"   ✅ Saved {len(data)} records to Supabase")
            print()
            print("   Run './check_supabase_data.sh' to see the new data!")
        except Exception as e:
            print(f"   ⚠️ Failed to save to Supabase: {e}")
        
    else:
        print("⚠️ WARNING: Provider captured but unexpected format")
        print(f"   Got: '{provider}'")
        print(f"   Expected: Something with 'Корт' in it")
    
    await db.close()
    print()

if __name__ == '__main__':
    asyncio.run(test_provider_capture())
