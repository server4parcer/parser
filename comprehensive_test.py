#!/usr/bin/env python3
"""
Comprehensive deployment test - check current vs new version
"""
import requests
import time
import json
from datetime import datetime

BASE_URL = "https://server4parcer-parser-4949.twc1.net"

def check_version_details():
    """Check which version is currently deployed"""
    print("🔍 Checking current deployment version...")
    
    try:
        # Health check
        health = requests.get(f"{BASE_URL}/health", timeout=10).json()
        print(f"📊 Current Version: {health.get('version', 'Unknown')}")
        print(f"📊 Production Ready: {health.get('production_ready', False)}")
        
        # Check for lightweight parser indicators
        parsing_method = health.get('parsing_method')
        browser_deps = health.get('browser_dependencies')
        
        if parsing_method or browser_deps is not None:
            print(f"✅ NEW VERSION DETECTED!")
            print(f"   Parsing Method: {parsing_method}")
            print(f"   Browser Dependencies: {browser_deps}")
            return "new"
        else:
            print(f"⚠️ OLD VERSION STILL RUNNING")
            return "old"
            
    except Exception as e:
        print(f"❌ Error checking version: {e}")
        return "error"

def test_parser_functionality():
    """Test parser functionality regardless of version"""
    print("\n🧪 Testing parser functionality...")
    
    try:
        # Test manual parser run
        print("🎯 Testing manual parser run...")
        run_response = requests.post(f"{BASE_URL}/parser/run", timeout=30)
        
        if run_response.status_code == 200:
            result = run_response.json()
            print(f"✅ Parser run successful!")
            print(f"   Status: {result.get('status', 'Unknown')}")
            print(f"   Extracted: {result.get('extracted', 0)} records")
            
            # Wait a moment and check data
            time.sleep(3)
            
            # Check if data was extracted
            data_response = requests.get(f"{BASE_URL}/api/booking-data", timeout=10)
            if data_response.status_code == 200:
                data_result = data_response.json()
                records = data_result.get('data', [])
                print(f"✅ Data API working: {len(records)} records available")
                
                if records:
                    print(f"📝 Sample record:")
                    sample = records[0]
                    print(f"   Date: {sample.get('date', 'N/A')}")
                    print(f"   Time: {sample.get('time', 'N/A')}")
                    print(f"   Price: {sample.get('price', 'N/A')}")
                    print(f"   Provider: {sample.get('provider', 'N/A')}")
                    return True
                else:
                    print(f"⚠️ No data records found")
                    return False
            else:
                print(f"❌ Data API failed: {data_response.status_code}")
                return False
        else:
            print(f"❌ Parser run failed: {run_response.status_code}")
            print(f"   Response: {run_response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Parser test error: {e}")
        return False

def wait_for_new_deployment(max_minutes=10):
    """Wait for new deployment to appear"""
    print(f"\n⏳ Waiting up to {max_minutes} minutes for new deployment...")
    
    attempts = max_minutes * 2  # Check every 30 seconds
    
    for attempt in range(1, attempts + 1):
        print(f"⏱️ Attempt {attempt}/{attempts} - {datetime.now().strftime('%H:%M:%S')}")
        
        version = check_version_details()
        
        if version == "new":
            print("🎉 NEW LIGHTWEIGHT VERSION DETECTED!")
            return True
        elif version == "old":
            print("⚠️ Still old version, waiting...")
        else:
            print("❌ Error checking version")
        
        if attempt < attempts:
            print("   Waiting 30 seconds...")
            time.sleep(30)
    
    print(f"⏰ Timeout: New version not deployed after {max_minutes} minutes")
    return False

def main():
    print("🚀 COMPREHENSIVE DEPLOYMENT TEST")
    print("=" * 50)
    
    # Check current version
    current_version = check_version_details()
    
    if current_version == "new":
        print("✅ New lightweight version already deployed!")
        test_parser_functionality()
    elif current_version == "old":
        print("⚠️ Old version detected. Testing current functionality first...")
        
        # Test current functionality
        current_works = test_parser_functionality()
        
        if current_works:
            print("✅ Current version is functional")
        else:
            print("❌ Current version has issues")
        
        # Wait for new deployment
        new_deployed = wait_for_new_deployment(8)  # 8 minutes max
        
        if new_deployed:
            print("\n🎉 NEW VERSION DEPLOYED! Testing new functionality...")
            test_parser_functionality()
        else:
            print("\n⚠️ New version not deployed yet. Current version is still running.")
            print("💡 You can manually check TimeWeb dashboard for build logs.")
    else:
        print("❌ Unable to determine version status")
    
    print("\n" + "=" * 50)
    print("📊 FINAL STATUS:")
    final_version = check_version_details()
    if final_version == "new":
        print("✅ Lightweight parser deployed and working!")
    elif final_version == "old":
        print("⚠️ Old version still running (deployment may be in progress)")
    else:
        print("❌ Version status unclear")

if __name__ == "__main__":
    main()
