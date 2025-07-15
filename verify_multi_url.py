#!/usr/bin/env python3
"""
🔍 MULTI-URL DEPLOYMENT VERIFICATION SCRIPT
Run this AFTER updating TimeWeb environment variables to verify multi-URL functionality
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "https://server4parcer-parser-4949.twc1.net"

def verify_multi_url_configuration():
    """Verify that multiple URLs are configured"""
    print("🔍 VERIFYING MULTI-URL CONFIGURATION")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/urls", timeout=10)
        if response.status_code == 200:
            data = response.json()
            urls = data.get("urls", [])
            count = data.get("count", 0)
            
            print(f"✅ URLs Configured: {count}")
            
            if count >= 6:
                print(f"🎉 SUCCESS: Multi-URL configuration detected!")
                for i, url in enumerate(urls, 1):
                    # Determine venue name
                    venue_name = "Unknown"
                    if "1192304" in url:
                        venue_name = "Корты-Сетки"
                    elif "select-city" in url:
                        venue_name = "Lunda Padel (Multi-location)"
                    elif "1109937" in url:
                        venue_name = "Нагатинская"
                    elif "804153" in url:
                        venue_name = "Padel Friends"
                    elif "936902" in url:
                        venue_name = 'ТК "Ракетлон"'
                    elif "855029" in url:
                        venue_name = "Padel A33"
                    
                    print(f"   {i}. {venue_name}")
                    print(f"      {url}")
                
                return True, count, urls
            elif count > 1:
                print(f"⚠️ PARTIAL: {count} URLs configured (expected 6)")
                return True, count, urls
            else:
                print(f"❌ SINGLE URL: Only {count} URL configured")
                print(f"   This means the TimeWeb update hasn't been applied yet")
                return False, count, urls
        else:
            print(f"❌ Configuration check failed: HTTP {response.status_code}")
            return False, 0, []
            
    except Exception as e:
        print(f"❌ Error checking configuration: {e}")
        return False, 0, []

def test_multi_url_parsing():
    """Test parser with multiple URLs"""
    print(f"\n🧪 TESTING MULTI-URL PARSING")
    print("=" * 50)
    
    try:
        print(f"🚀 Triggering parser run...")
        start_time = time.time()
        
        response = requests.post(f"{BASE_URL}/parser/run", timeout=60)  # Longer timeout for multiple URLs
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "unknown")
            extracted = data.get("extracted", 0)
            parse_time = time.time() - start_time
            
            print(f"✅ Parser Status: {status}")
            print(f"✅ Records Extracted: {extracted}")
            print(f"✅ Parse Time: {parse_time:.1f} seconds")
            
            if extracted >= 10:  # Expect more records with multiple URLs
                print(f"🎉 SUCCESS: Multi-URL parsing working! ({extracted} records)")
                return True, extracted
            elif extracted > 3:  # Some improvement
                print(f"⚠️ PARTIAL: Some improvement ({extracted} vs ~3 before)")
                return True, extracted
            else:
                print(f"❌ NO IMPROVEMENT: Still only {extracted} records")
                return False, extracted
        else:
            print(f"❌ Parser run failed: HTTP {response.status_code}")
            return False, 0
            
    except Exception as e:
        print(f"❌ Parser test error: {e}")
        return False, 0

def verify_multi_venue_data():
    """Verify data from multiple venues"""
    print(f"\n📊 VERIFYING MULTI-VENUE DATA")
    print("=" * 50)
    
    try:
        # Wait for data to be processed
        time.sleep(5)
        
        response = requests.get(f"{BASE_URL}/api/booking-data?limit=50", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            records = data.get("data", [])
            
            print(f"✅ Total Records Available: {len(records)}")
            
            if records:
                # Analyze venues
                venues = set()
                urls = set()
                providers = set()
                
                for record in records:
                    if "location_name" in record:
                        venues.add(record["location_name"])
                    if "url" in record:
                        urls.add(record["url"])
                    if "provider" in record:
                        providers.add(record["provider"])
                
                print(f"✅ Venues Covered: {len(venues)}")
                for venue in sorted(venues):
                    print(f"   - {venue}")
                
                print(f"✅ URLs Processed: {len(urls)}")
                print(f"✅ Unique Providers: {len(providers)}")
                
                # Show sample records
                print(f"\n📝 Sample Records:")
                for i, record in enumerate(records[:3], 1):
                    print(f"   {i}. {record.get('date', 'N/A')} {record.get('time', 'N/A')}")
                    print(f"      Price: {record.get('price', 'N/A')}")
                    print(f"      Provider: {record.get('provider', 'N/A')}")
                    print(f"      Location: {record.get('location_name', 'N/A')}")
                
                if len(venues) >= 3:
                    print(f"\n🎉 SUCCESS: Multi-venue data confirmed!")
                    return True, len(venues), len(records)
                elif len(venues) > 1:
                    print(f"\n⚠️ PARTIAL: {len(venues)} venues detected")
                    return True, len(venues), len(records)
                else:
                    print(f"\n❌ SINGLE VENUE: Only 1 venue in data")
                    return False, len(venues), len(records)
            else:
                print(f"❌ No data records found")
                return False, 0, 0
        else:
            print(f"❌ Data retrieval failed: HTTP {response.status_code}")
            return False, 0, 0
            
    except Exception as e:
        print(f"❌ Data verification error: {e}")
        return False, 0, 0

def generate_verification_report():
    """Generate comprehensive verification report"""
    print(f"\n📋 GENERATING VERIFICATION REPORT")
    print("=" * 50)
    
    # Run all verifications
    config_ok, url_count, configured_urls = verify_multi_url_configuration()
    parser_ok, extracted_count = test_multi_url_parsing()
    data_ok, venue_count, record_count = verify_multi_venue_data()
    
    # Overall success
    overall_success = config_ok and parser_ok and data_ok and url_count >= 6
    
    report = {
        "verification_report": {
            "timestamp": datetime.now().isoformat(),
            "overall_success": overall_success,
            "configuration": {
                "urls_configured": url_count,
                "expected_urls": 6,
                "status": "success" if url_count >= 6 else "pending" if url_count > 1 else "failed"
            },
            "parsing": {
                "records_extracted": extracted_count,
                "status": "success" if extracted_count >= 10 else "partial" if extracted_count > 3 else "failed"
            },
            "data_quality": {
                "venues_covered": venue_count,
                "total_records": record_count,
                "status": "success" if venue_count >= 3 else "partial" if venue_count > 1 else "failed"
            },
            "configured_urls": configured_urls,
            "recommendations": []
        }
    }
    
    # Add recommendations
    if not overall_success:
        if url_count < 6:
            report["verification_report"]["recommendations"].append(
                "Update TimeWeb PARSE_URLS environment variable with all 6 URLs"
            )
        if extracted_count < 10:
            report["verification_report"]["recommendations"].append(
                "Wait for parser to process all URLs, then test again"
            )
        if venue_count < 3:
            report["verification_report"]["recommendations"].append(
                "Verify URLs are accessible and parser logic handles different venue formats"
            )
    
    # Save report
    with open("multi_url_verification_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report

def main():
    """Main verification process"""
    print("🔍 MULTI-URL DEPLOYMENT VERIFICATION")
    print("=" * 70)
    print(f"🕐 Verification Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 System: {BASE_URL}")
    print(f"🎯 Expected: 6 URLs, multiple venues, 10+ records")
    
    # Generate comprehensive report
    report = generate_verification_report()
    
    # Display results
    print(f"\n" + "=" * 70)
    print("📊 VERIFICATION RESULTS SUMMARY")
    print("=" * 70)
    
    verification = report["verification_report"]
    
    # Configuration status
    config = verification["configuration"]
    config_status = "✅" if config["status"] == "success" else "⚠️" if config["status"] == "partial" else "❌"
    print(f"{config_status} Configuration: {config['urls_configured']}/6 URLs configured")
    
    # Parser status
    parsing = verification["parsing"]
    parse_status = "✅" if parsing["status"] == "success" else "⚠️" if parsing["status"] == "partial" else "❌"
    print(f"{parse_status} Parsing: {parsing['records_extracted']} records extracted")
    
    # Data quality status
    data_quality = verification["data_quality"]
    data_status = "✅" if data_quality["status"] == "success" else "⚠️" if data_quality["status"] == "partial" else "❌"
    print(f"{data_status} Data Quality: {data_quality['venues_covered']} venues, {data_quality['total_records']} records")
    
    # Overall status
    overall_success = verification["overall_success"]
    overall_status = "✅" if overall_success else "❌"
    print(f"\n{overall_status} OVERALL STATUS: {'SUCCESS' if overall_success else 'NEEDS ATTENTION'}")
    
    # Recommendations
    recommendations = verification["recommendations"]
    if recommendations:
        print(f"\n🔧 RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    
    # Next steps
    if overall_success:
        print(f"\n🎉 MULTI-URL DEPLOYMENT SUCCESSFUL!")
        print(f"✅ System is now processing {config['urls_configured']} venues")
        print(f"✅ Extracting data from multiple locations")
        print(f"✅ Ready for production use with all Pavel's venues")
        
        print(f"\n📊 Current Performance:")
        print(f"   URLs: {config['urls_configured']} venues")
        print(f"   Records: {parsing['records_extracted']} per run")
        print(f"   Venues: {data_quality['venues_covered']} locations")
        print(f"   Update Frequency: Every 10 minutes")
        
    else:
        print(f"\n⚠️ MULTI-URL DEPLOYMENT INCOMPLETE")
        print(f"📋 Current Status:")
        print(f"   URLs Configured: {config['urls_configured']}/6")
        print(f"   Records Extracted: {parsing['records_extracted']}")
        print(f"   Venues Covered: {data_quality['venues_covered']}")
        
        if config['urls_configured'] < 6:
            print(f"\n🚀 TO COMPLETE DEPLOYMENT:")
            print(f"1. Go to TimeWeb → Apps → YC-parser → Environment Variables")
            print(f"2. Update PARSE_URLS with all 6 URLs from TIMEWEB_UPDATE_INSTRUCTIONS.md")
            print(f"3. Save and wait 2-3 minutes for restart")
            print(f"4. Run this verification script again")
    
    print(f"\n📋 Report saved: multi_url_verification_report.json")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Multi-URL deployment verified successfully!")
    else:
        print("\n⚠️ Multi-URL deployment needs completion.")
