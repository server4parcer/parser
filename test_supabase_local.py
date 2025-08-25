#!/usr/bin/env python3
"""
LOCAL TEST - Same Supabase logic as TimeWeb to debug save failures
"""
import os
from datetime import datetime
from supabase import create_client

# Use EXACT same credentials as TimeWeb
SUPABASE_URL = "https://axedyenlcdfrjhwfcokj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF4ZWR5ZW5sY2RmcmpoZmNva2oiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTcxNzczMjU3NSwiZXhwIjoyMDMzMzA4NTc1fQ.xQrNXHJt5N3DgQzN8rOGP3qOz1c-LL-7dV7ZgAQe3d0"

print("🔍 LOCAL SUPABASE TEST")
print(f"URL: {SUPABASE_URL}")
print(f"Key: {SUPABASE_KEY[:20]}...")

# Initialize Supabase (exact same as TimeWeb)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✅ Supabase client created")

# Test connection
try:
    result = supabase.table('booking_data').select("*").limit(1).execute()
    print(f"✅ Table exists, found {len(result.data)} existing records")
except Exception as e:
    print(f"❌ Table check error: {e}")

# Create same test data as TimeWeb
test_booking = {
    "venue_name": "LOCAL_TEST",
    "date": "2025-08-23",
    "time": "10:00",
    "price": "TEST - Local debugging",
    "duration": 60,
    "court_name": "Debug Entry",
    "source_url": "local_test"
}

print(f"📤 Attempting to insert: {test_booking}")

# Try to save (exact same logic)
try:
    result = supabase.table('booking_data').insert([test_booking]).execute()
    print(f"✅ SUCCESS! Saved to Supabase: {result.data}")
    saved_count = len(result.data) if result.data else 0
    print(f"📊 Saved count: {saved_count}")
except Exception as e:
    print(f"❌ INSERT ERROR: {e}")
    print(f"📊 Error type: {type(e)}")
    import traceback
    traceback.print_exc()

print("\n🎯 COMPARISON:")
print("If this works locally but fails on TimeWeb = TimeWeb environment issue")
print("If this fails locally too = Supabase configuration issue")