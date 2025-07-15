#!/usr/bin/env python3
"""
🎯 MULTI-URL TESTING SCRIPT FOR PAVEL'S YCLIENTS URLS
Test all Pavel's URLs and verify multi-URL functionality on TimeWeb
"""
import requests
import json
import time
from datetime import datetime
from urllib.parse import urlparse

# Pavel's YClients URLs
PAVEL_URLS = [
    "https://n1308467.yclients.com/company/1192304/record-type?o=",  # Корты-Сетки
    "https://b911781.yclients.com/select-city/2/select-branch?o=",    # Multi-location (3 addresses)
    "https://n1165596.yclients.com/company/1109937/record-type?o=",  # Current working URL
    "https://b861100.yclients.com/company/804153/personal/select-time?o=m-1",  # Padel Friends
    "https://b1009933.yclients.com/company/936902/personal/select-time?o=",     # ТК "Ракетлон"
    "https://b918666.yclients.com/company/855029/personal/menu?o=m-1"           # Padel A33
]

BASE_URL = "https://server4parcer-parser-4949.twc1.net"

def test_individual_url_parsing():
    """Test each URL individually to check accessibility"""
    print("🔍 TESTING INDIVIDUAL URL ACCESSIBILITY")
    print("=" * 60)
    
    results = []
    
    for i, url in enumerate(PAVEL_URLS, 1):
        print(f"\n🎯 Testing URL {i}/6: {url}")
        
        # Extract venue name from URL
        if "1192304" in url:
            venue = "Корты-Сетки"
        elif "select-city" in url:
            venue = "Multi-location (3 clubs)"  
        elif "1109937" in url:
            venue = "Current working venue"
        elif "804153" in url:
            venue = "Padel Friends"
        elif "936902" in url:
            venue = 'ТК "Ракетлон"'
        elif "855029" in url:
            venue = "Padel A33"
        else:
            venue = "Unknown venue"
        
        print(f"   📍 Venue: {venue}")
        
        try:
            # Test direct access
            response = requests.get(url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            status_code = response.status_code
            content_length = len(response.content)
            
            print(f"   📊 HTTP Status: {status_code}")
            print(f"   📏 Content Size: {content_length:,} bytes")
            
            if status_code == 200:
                # Check for common YClients elements
                content = response.text.lower()
                indicators = {
                    "booking_system": "yclients" in content or "booking" in content,
                    "time_slots": "time" in content or "час" in content,
                    "prices": "₽" in content or "руб" in content,
                    "courts": "корт" in content or "зал" in content or "площадка" in content
                }
                
                print(f"   🔍 Content Analysis:")
                for indicator, found in indicators.items():
                    status = "✅" if found else "❌"
                    print(f"     {status} {indicator}: {found}")
                
                result = {
                    "url": url,
                    "venue": venue,
                    "accessible": True,
                    "status_code": status_code,
                    "content_size": content_length,
                    "indicators": indicators,
                    "parseable": any(indicators.values())
                }
            else:
                result = {
                    "url": url,
                    "venue": venue, 
                    "accessible": False,
                    "status_code": status_code,
                    "error": f"HTTP {status_code}"
                }
                print(f"   ❌ Not accessible: HTTP {status_code}")
                
        except Exception as e:
            result = {
                "url": url,
                "venue": venue,
                "accessible": False,
                "error": str(e)
            }
            print(f"   ❌ Error: {e}")
        
        results.append(result)
        
        # Small delay between requests
        time.sleep(2)
    
    return results

def test_current_timeweb_system():
    """Test current TimeWeb system status"""
    print("\n🏥 TESTING CURRENT TIMEWEB SYSTEM")
    print("=" * 60)
    
    try:
        # Health check
        health = requests.get(f"{BASE_URL}/health", timeout=10).json()
        print(f"✅ System Health: {health.get('status', 'Unknown')}")
        print(f"   Version: {health.get('version', 'Unknown')}")
        print(f"   Production Ready: {health.get('production_ready', False)}")
        
        # Current configuration
        urls_config = requests.get(f"{BASE_URL}/api/urls", timeout=10).json()
        current_urls = urls_config.get("urls", [])
        
        print(f"\n📋 Current Configuration:")
        print(f"   URLs Configured: {len(current_urls)}")
        for i, url in enumerate(current_urls, 1):
            print(f"   {i}. {url}")
        
        # Test current parser
        print(f"\n🧪 Testing Current Parser...")
        parser_result = requests.post(f"{BASE_URL}/parser/run", timeout=30).json()
        print(f"   Status: {parser_result.get('status', 'Unknown')}")
        print(f"   Extracted: {parser_result.get('extracted', 0)} records")
        
        # Get current data
        time.sleep(3)
        data_result = requests.get(f"{BASE_URL}/api/booking-data?limit=5", timeout=10).json()
        current_records = data_result.get("data", [])
        
        print(f"\n📊 Current Data:")
        print(f"   Total Records: {len(current_records)}")
        
        if current_records:
            sample = current_records[0]
            print(f"   Sample Record:")
            print(f"     Date: {sample.get('date', 'N/A')}")
            print(f"     Time: {sample.get('time', 'N/A')}")
            print(f"     Price: {sample.get('price', 'N/A')}")
            print(f"     Provider: {sample.get('provider', 'N/A')}")
        
        return True, current_urls, current_records
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False, [], []

def create_multi_url_test_configuration():
    """Create test configuration with Pavel's URLs"""
    print("\n⚙️ PREPARING MULTI-URL CONFIGURATION")
    print("=" * 60)
    
    # Create comma-separated URL string for environment variable
    url_string = ",".join(PAVEL_URLS)
    
    print(f"📋 Environment Variable Configuration:")
    print(f"PARSE_URLS={url_string}")
    print(f"\n📊 URLs Summary:")
    
    for i, url in enumerate(PAVEL_URLS, 1):
        venue_name = ""
        if "1192304" in url:
            venue_name = "Корты-Сетки"
        elif "select-city" in url:
            venue_name = "Multi-location"
        elif "1109937" in url:
            venue_name = "Working venue"
        elif "804153" in url:
            venue_name = "Padel Friends"
        elif "936902" in url:
            venue_name = 'ТК "Ракетлон"'
        elif "855029" in url:
            venue_name = "Padel A33"
        
        print(f"   {i}. {venue_name}: {url}")
    
    print(f"\n💡 TO UPDATE TIMEWEB:")
    print(f"1. Go to TimeWeb → Apps → YC-parser → Environment Variables")
    print(f"2. Edit PARSE_URLS variable")
    print(f"3. Replace with: {url_string}")
    print(f"4. Save changes")
    print(f"5. Wait 2-3 minutes for restart")
    
    return url_string

def simulate_multi_url_parsing():
    """Simulate what the parser would do with multiple URLs"""
    print("\n🔄 SIMULATING MULTI-URL PARSING")
    print("=" * 60)
    
    all_results = []
    
    # Simulate parsing each URL
    for i, url in enumerate(PAVEL_URLS, 1):
        print(f"\n🎯 Simulating parse of URL {i}/6...")
        
        # Determine venue info
        venue_info = {
            "1192304": {"name": "Корты-Сетки", "location": "3-я Мытищинская улица, 16"},
            "select-city": {"name": "Lunda Padel", "location": "Multiple locations"},
            "1109937": {"name": "Нагатинская", "location": "1-й Нагатинский проезд, 2"},
            "804153": {"name": "Padel Friends", "location": "ул. Лужники, 24"},
            "936902": {"name": 'ТК "Ракетлон"', "location": "улица Лобачевского, 138"},
            "855029": {"name": "Padel A33", "location": "Мытищи, Трудовая улица, 33"}
        }
        
        # Find venue
        venue = {"name": "Unknown", "location": "Unknown"}
        for key, info in venue_info.items():
            if key in url:
                venue = info
                break
        
        # Simulate extracted data
        simulated_records = []
        base_times = ["10:00", "12:00", "14:00", "16:00", "18:00"]
        base_prices = [2500, 3000, 3500, 4000, 4500]
        
        for j, (time_slot, price) in enumerate(zip(base_times, base_prices)):
            record = {
                "url": url,
                "date": "2025-06-28",
                "time": time_slot,
                "price": f"{price} ₽",
                "provider": f"{venue['name']} - Корт №{j+1}",
                "seat_number": str(j+1),
                "location_name": venue["name"],
                "court_type": "PADEL" if "padel" in venue["name"].lower() else "TENNIS",
                "time_category": "ДЕНЬ" if int(time_slot.split(':')[0]) < 17 else "ВЕЧЕР",
                "duration": 60,
                "review_count": 5 + j,
                "prepayment_required": True,
                "extracted_at": datetime.now().isoformat()
            }
            simulated_records.append(record)
        
        print(f"   ✅ Simulated {len(simulated_records)} records from {venue['name']}")
        all_results.extend(simulated_records)
    
    print(f"\n📊 SIMULATION SUMMARY:")
    print(f"   Total URLs: {len(PAVEL_URLS)}")
    print(f"   Total Records: {len(all_results)}")
    print(f"   Records per URL: ~{len(all_results)//len(PAVEL_URLS)}")
    
    # Group by venue
    venues = {}
    for record in all_results:
        venue_name = record["location_name"]
        if venue_name not in venues:
            venues[venue_name] = 0
        venues[venue_name] += 1
    
    print(f"\n📍 Records by Venue:")
    for venue, count in venues.items():
        print(f"   {venue}: {count} records")
    
    return all_results

def create_comprehensive_test_report():
    """Create comprehensive test report"""
    print("\n📋 GENERATING COMPREHENSIVE TEST REPORT")
    print("=" * 60)
    
    # Run all tests
    url_results = test_individual_url_parsing()
    system_ok, current_urls, current_data = test_current_timeweb_system()
    config_string = create_multi_url_test_configuration()
    simulated_data = simulate_multi_url_parsing()
    
    # Calculate success metrics
    accessible_urls = [r for r in url_results if r.get("accessible", False)]
    parseable_urls = [r for r in url_results if r.get("parseable", False)]
    
    report = {
        "test_report": {
            "timestamp": datetime.now().isoformat(),
            "test_type": "Multi-URL functionality verification",
            "pavel_urls": PAVEL_URLS,
            "summary": {
                "total_urls": len(PAVEL_URLS),
                "accessible_urls": len(accessible_urls),
                "parseable_urls": len(parseable_urls),
                "success_rate": f"{len(accessible_urls)/len(PAVEL_URLS)*100:.1f}%",
                "system_operational": system_ok
            },
            "url_analysis": url_results,
            "current_system": {
                "working": system_ok,
                "current_urls": current_urls,
                "current_data_count": len(current_data),
                "sample_data": current_data[:2] if current_data else []
            },
            "multi_url_config": {
                "environment_variable": config_string,
                "setup_instructions": [
                    "Go to TimeWeb → Apps → YC-parser → Environment Variables",
                    "Edit PARSE_URLS variable", 
                    f"Replace with: {config_string}",
                    "Save changes",
                    "Wait 2-3 minutes for restart"
                ]
            },
            "simulated_results": {
                "total_records": len(simulated_data),
                "venues_covered": len(set(r["location_name"] for r in simulated_data)),
                "sample_records": simulated_data[:3]
            },
            "recommendations": []
        }
    }
    
    # Add recommendations
    if len(accessible_urls) < len(PAVEL_URLS):
        report["test_report"]["recommendations"].append(
            "Some URLs not accessible - may need specific navigation logic"
        )
    
    if system_ok:
        report["test_report"]["recommendations"].append(
            "System ready for multi-URL deployment"
        )
    else:
        report["test_report"]["recommendations"].append(
            "Fix current system issues before adding more URLs"
        )
    
    # Save report
    with open("multi_url_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report

def main():
    """Main test execution"""
    print("🎯 PAVEL'S YCLIENTS URLS - MULTI-URL TESTING")
    print("=" * 70)
    print(f"🕐 Test Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 TimeWeb System: {BASE_URL}")
    print(f"📊 Total URLs to Test: {len(PAVEL_URLS)}")
    
    # Generate comprehensive report
    report = create_comprehensive_test_report()
    
    # Display summary
    print("\n" + "=" * 70)
    print("📊 MULTI-URL TEST RESULTS SUMMARY")
    print("=" * 70)
    
    summary = report["test_report"]["summary"]
    print(f"📋 Total URLs: {summary['total_urls']}")
    print(f"✅ Accessible: {summary['accessible_urls']}")
    print(f"🔍 Parseable: {summary['parseable_urls']}")
    print(f"📈 Success Rate: {summary['success_rate']}")
    print(f"🏥 System Status: {'✅ Operational' if summary['system_operational'] else '❌ Issues'}")
    
    print(f"\n📍 VENUE ANALYSIS:")
    for i, url_result in enumerate(report["test_report"]["url_analysis"], 1):
        venue = url_result["venue"]
        accessible = "✅" if url_result.get("accessible", False) else "❌"
        print(f"   {i}. {accessible} {venue}")
    
    # Show configuration
    config = report["test_report"]["multi_url_config"]
    print(f"\n⚙️ MULTI-URL CONFIGURATION READY:")
    print(f"   Environment Variable: PARSE_URLS")
    print(f"   URLs Count: {len(PAVEL_URLS)}")
    print(f"   Total Length: {len(config['environment_variable'])} characters")
    
    # Show simulated results
    sim_results = report["test_report"]["simulated_results"]
    print(f"\n🔄 SIMULATION RESULTS:")
    print(f"   Estimated Records: {sim_results['total_records']}")
    print(f"   Venues Covered: {sim_results['venues_covered']}")
    print(f"   Records per URL: ~{sim_results['total_records']//len(PAVEL_URLS)}")
    
    print(f"\n📋 Report saved: multi_url_test_report.json")
    
    # Final recommendation
    accessible_count = summary["accessible_urls"]
    if accessible_count >= 4 and summary["system_operational"]:
        print(f"\n🎉 READY FOR MULTI-URL DEPLOYMENT!")
        print(f"✅ {accessible_count}/{summary['total_urls']} URLs accessible")
        print(f"✅ System operational and ready")
        print(f"✅ Configuration prepared")
        
        print(f"\n🚀 NEXT STEPS:")
        print(f"1. Update TimeWeb environment variable")
        print(f"2. Wait for system restart")
        print(f"3. Test multi-URL parsing")
        print(f"4. Verify data from all venues")
        
    else:
        print(f"\n⚠️ ISSUES DETECTED:")
        if accessible_count < 4:
            print(f"❌ Only {accessible_count}/{summary['total_urls']} URLs accessible")
        if not summary["system_operational"]:
            print(f"❌ System not operational")
        
        print(f"\n🔧 RECOMMENDATIONS:")
        print(f"1. Fix URL accessibility issues")
        print(f"2. Ensure system is operational")
        print(f"3. Test incrementally with working URLs first")

if __name__ == "__main__":
    main()
