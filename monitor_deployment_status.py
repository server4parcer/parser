#!/usr/bin/env python3
import requests
import time
from datetime import datetime

BASE_URL = "https://server4parcer-parser-4949.twc1.net"

def check_deployment_status():
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return True, data
        else:
            return False, {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return False, {"error": str(e)}

def monitor_deployment():
    print("🔍 MONITORING TIMEWEB DEPLOYMENT")
    print("=" * 50)
    print(f"URL: {BASE_URL}")
    print("Waiting for deployment to complete...")
    print()
    
    attempt = 1
    max_attempts = 30
    
    while attempt <= max_attempts:
        print(f"Attempt {attempt:2d}/{max_attempts} - {datetime.now().strftime('%H:%M:%S')}", end=" ")
        
        success, data = check_deployment_status()
        
        if success:
            print("✅ DEPLOYMENT READY!")
            print(f"   Status: {data.get('status', 'Unknown')}")
            print(f"   Parser: {data.get('parser_type', 'Unknown')}")
            print(f"   Supabase: {data.get('supabase_connected', 'Unknown')}")
            
            if data.get('parser_type') == 'playwright':
                print("🎭 PLAYWRIGHT PARSER DETECTED!")
            elif 'playwright' in str(data.get('parser_type', '')).lower():
                print("🎭 Playwright-based parser active")
            else:
                print(f"⚠️ Parser type: {data.get('parser_type')} (expected Playwright)")
            
            return True
        else:
            print(f"❌ {data.get('error', 'Unknown error')}")
        
        if attempt < max_attempts:
            print("   ⏳ Waiting 10 seconds...")
            time.sleep(10)
        
        attempt += 1
    
    print(f"\n❌ Deployment not ready after {max_attempts} attempts")
    print("💡 Check TimeWeb dashboard for build status")
    return False

if __name__ == "__main__":
    success = monitor_deployment()
    if success:
        print(f"\n🚀 Run test: python test_pavel_deployment.py")
    else:
        print(f"\n⏰ Try again in 5-10 minutes")