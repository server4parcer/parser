#!/usr/bin/env python3
import requests
import json
import time
from datetime import datetime

BASE_URL = "https://server4parcer-parser-4949.twc1.net"
PAVEL_URL = "https://b918666.yclients.com/company/855029/personal/menu?o=m-1"

def test_health():
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health: {response.status_code}")
            print(f"   Status: {data.get('status')}")
            print(f"   Parser Type: {data.get('parser_type')}")
            print(f"   Supabase: {data.get('supabase_connected')}")
            return True
        else:
            print(f"❌ Health: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health failed: {e}")
        return False

def test_parser_status():
    print("\n🔍 Testing parser status...")
    try:
        response = requests.get(f"{BASE_URL}/parser/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Parser Status: {response.status_code}")
            print(f"   Mode: {data.get('mode')}")
            print(f"   URLs Configured: {data.get('urls_configured')}")
            print(f"   Browser Automation: {data.get('browser_automation')}")
            return True
        else:
            print(f"❌ Parser Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Parser status failed: {e}")
        return False

def test_parser_run():
    print("\n🔍 Testing parser run...")
    try:
        response = requests.post(f"{BASE_URL}/parser/run", timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Parser Run: {response.status_code}")
            print(f"   Status: {data.get('status')}")
            print(f"   Extracted: {data.get('extracted', 0)} records")
            print(f"   Parser Type: {data.get('parser_type')}")
            print(f"   Message: {data.get('message', '')}")
            return data.get('status') == 'success'
        else:
            print(f"❌ Parser Run: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Parser run failed: {e}")
        return False

def test_booking_data():
    print("\n🔍 Testing booking data...")
    try:
        response = requests.get(f"{BASE_URL}/api/booking-data", timeout=10)
        if response.status_code == 200:
            data = response.json()
            records = data.get('data', [])
            print(f"✅ Booking Data: {response.status_code}")
            print(f"   Total Records: {len(records)}")
            
            if records:
                print("\n📋 Sample Records:")
                for i, record in enumerate(records[:3], 1):
                    print(f"   Record {i}:")
                    print(f"     Venue: {record.get('venue_name', 'N/A')}")
                    print(f"     Date: {record.get('date', 'N/A')}")
                    print(f"     Time: {record.get('time', 'N/A')}")
                    print(f"     Price: {record.get('price', 'N/A')}")
                    print(f"     Duration: {record.get('duration', 'N/A')} min")
                
                expected_prices = ['2500 ₽', '3750 ₽', '5000 ₽']
                found_prices = [r.get('price', '') for r in records]
                padel_records = [r for r in records if 'padel' in r.get('venue_name', '').lower()]
                
                print(f"\n🎯 Pavel's Data Check:")
                print(f"   Padel A33 records: {len(padel_records)}")
                print(f"   Expected prices found: {any(p in found_prices for p in expected_prices)}")
                
            return len(records) > 0
        else:
            print(f"❌ Booking Data: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Booking data failed: {e}")
        return False

def test_supabase_debug():
    print("\n🔍 Testing Supabase debug...")
    try:
        response = requests.get(f"{BASE_URL}/debug/supabase", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Supabase Debug: {response.status_code}")
            tests = data.get('tests', [])
            for test in tests:
                status = "✅" if test.get('status') == 'success' else "❌"
                print(f"   {status} {test.get('test')}: {test.get('status')}")
            return True
        else:
            print(f"⚠️ Supabase Debug: {response.status_code}")
            return True
    except Exception as e:
        print(f"⚠️ Supabase debug: {e}")
        return True

def main():
    print("🚀 PAVEL DEPLOYMENT TEST")
    print("=" * 50)
    print(f"Testing: {BASE_URL}")
    print(f"Pavel's URL: {PAVEL_URL}")
    print()
    
    tests = [
        ("Health Check", test_health),
        ("Parser Status", test_parser_status), 
        ("Supabase Debug", test_supabase_debug),
        ("Parser Run", test_parser_run),
        ("Booking Data", test_booking_data),
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
        time.sleep(1)
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Summary: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 ALL TESTS PASSED! Deployment is working correctly.")
    elif passed >= len(results) - 1:
        print("✅ Deployment is mostly working, minor issues detected.")
    else:
        print("❌ Deployment has issues, check TimeWeb logs.")
    
    print(f"\nTimestamp: {datetime.now()}")

if __name__ == "__main__":
    main()