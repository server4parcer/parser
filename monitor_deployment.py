#!/usr/bin/env python3
"""
Monitor TimeWeb deployment and test functionality
"""
import requests
import time
import json
from datetime import datetime

def test_endpoint(url, description):
    """Test an endpoint and return status"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"✅ {description}: OK (200)")
            return True, response.json() if 'application/json' in response.headers.get('content-type', '') else response.text[:100]
        else:
            print(f"❌ {description}: HTTP {response.status_code}")
            return False, response.text[:100]
    except requests.exceptions.RequestException as e:
        print(f"❌ {description}: {str(e)}")
        return False, str(e)

def monitor_deployment():
    """Monitor deployment status"""
    base_url = "https://server4parcer-parser-4949.twc1.net"
    
    print("🕐 Monitoring TimeWeb deployment...")
    print(f"📡 Base URL: {base_url}")
    print("⏱️  Expected deployment time: 5-10 minutes")
    print("=" * 60)
    
    attempt = 1
    max_attempts = 20  # ~10 minutes with 30s intervals
    
    while attempt <= max_attempts:
        print(f"\n🔍 Attempt {attempt}/{max_attempts} - {datetime.now().strftime('%H:%M:%S')}")
        
        # Test basic health
        health_ok, health_data = test_endpoint(f"{base_url}/health", "Health Check")
        
        if health_ok:
            print("🎉 DEPLOYMENT SUCCESSFUL!")
            
            # Test additional endpoints
            test_endpoint(f"{base_url}/", "Main Page")
            test_endpoint(f"{base_url}/parser/status", "Parser Status")
            test_endpoint(f"{base_url}/api/booking-data", "Booking Data API")
            
            # Show health data
            if isinstance(health_data, dict):
                print(f"\n📊 Health Check Details:")
                print(f"   Version: {health_data.get('version', 'Unknown')}")
                print(f"   Parser Method: {health_data.get('parsing_method', 'Unknown')}")
                print(f"   Browser Dependencies: {health_data.get('browser_dependencies', 'Unknown')}")
                print(f"   Production Ready: {health_data.get('production_ready', 'Unknown')}")
                
                parser_info = health_data.get('parser', {})
                print(f"   URLs Configured: {parser_info.get('urls_configured', 0)}")
                print(f"   Total Extracted: {parser_info.get('total_extracted', 0)}")
                
                db_info = health_data.get('database', {})
                print(f"   Database Connected: {db_info.get('connected', False)}")
            
            print(f"\n🎯 NEXT STEPS:")
            print(f"1. Test parser: GET {base_url}/parser/run")
            print(f"2. View data: GET {base_url}/api/booking-data") 
            print(f"3. Monitor logs in TimeWeb dashboard")
            
            return True
        
        print(f"⏳ Waiting 30 seconds before next attempt...")
        time.sleep(30)
        attempt += 1
    
    print(f"\n❌ Deployment not ready after {max_attempts} attempts")
    print(f"🔧 Check TimeWeb dashboard for build logs")
    return False

if __name__ == "__main__":
    monitor_deployment()
