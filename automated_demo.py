#!/usr/bin/env python3
"""
🎯 AUTOMATED DEMO SCRIPT FOR CLIENT
YClients Parser - Production Verification & Demo

Run this script to verify all functionality and generate a demo report
"""
import requests
import json
import time
from datetime import datetime
import sys

# Configuration
BASE_URL = "https://server4parcer-parser-4949.twc1.net"
TESTS = []
RESULTS = {"passed": 0, "failed": 0, "total": 0}

def log_test(name, status, details="", expected="", actual=""):
    """Log test result"""
    global RESULTS
    RESULTS["total"] += 1
    
    if status:
        RESULTS["passed"] += 1
        status_icon = "✅"
        status_text = "PASS"
    else:
        RESULTS["failed"] += 1
        status_icon = "❌" 
        status_text = "FAIL"
    
    print(f"{status_icon} {name}: {status_text}")
    if details:
        print(f"   {details}")
    if expected and actual:
        print(f"   Expected: {expected}")
        print(f"   Actual: {actual}")
    print()
    
    TESTS.append({
        "name": name,
        "status": status_text,
        "details": details,
        "expected": expected,
        "actual": actual,
        "timestamp": datetime.now().isoformat()
    })

def test_system_health():
    """Test 1: System Health Check"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        
        if response.status_code != 200:
            log_test("System Health", False, f"HTTP {response.status_code}", "200", str(response.status_code))
            return False
        
        data = response.json()
        
        # Check version
        version = data.get("version", "")
        if not version.startswith("4."):
            log_test("System Health", False, "Wrong version", "4.x.x", version)
            return False
        
        # Check production ready
        prod_ready = data.get("production_ready", False)
        if not prod_ready:
            log_test("System Health", False, "Not production ready", "True", str(prod_ready))
            return False
        
        # Check parsing method (new feature)
        parsing_method = data.get("parsing_method", "")
        browser_deps = data.get("browser_dependencies", True)
        
        details = f"Version: {version}, Production: {prod_ready}"
        if parsing_method:
            details += f", Method: {parsing_method}, Browser Deps: {browser_deps}"
        
        log_test("System Health", True, details)
        return True
        
    except Exception as e:
        log_test("System Health", False, f"Exception: {str(e)}")
        return False

def test_api_endpoints():
    """Test 2: All API Endpoints"""
    endpoints = [
        ("/", "Main Dashboard"),
        ("/parser/status", "Parser Status"),
        ("/api/booking-data", "Booking Data"),
        ("/api/urls", "URL Configuration"),
        ("/docs", "API Documentation")
    ]
    
    all_passed = True
    details = []
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                details.append(f"{name}: ✅")
            else:
                details.append(f"{name}: ❌ HTTP {response.status_code}")
                all_passed = False
        except Exception as e:
            details.append(f"{name}: ❌ {str(e)}")
            all_passed = False
    
    log_test("API Endpoints", all_passed, "; ".join(details))
    return all_passed

def test_parser_functionality():
    """Test 3: Parser Functionality"""
    try:
        # Trigger manual parser run
        print("   🔄 Running parser manually...")
        response = requests.post(f"{BASE_URL}/parser/run", timeout=30)
        
        if response.status_code != 200:
            log_test("Parser Functionality", False, f"Parser run failed: HTTP {response.status_code}")
            return False
        
        result = response.json()
        status = result.get("status", "")
        extracted = result.get("extracted", 0)
        
        if status != "success":
            log_test("Parser Functionality", False, f"Parser status: {status}", "success", status)
            return False
        
        # Wait and check data
        print("   ⏳ Waiting for data processing...")
        time.sleep(3)
        
        # Get booking data
        data_response = requests.get(f"{BASE_URL}/api/booking-data", timeout=10)
        if data_response.status_code != 200:
            log_test("Parser Functionality", False, f"Data API failed: HTTP {data_response.status_code}")
            return False
        
        data_result = data_response.json()
        records = data_result.get("data", [])
        
        if len(records) == 0:
            log_test("Parser Functionality", False, "No data records found", ">0 records", "0 records")
            return False
        
        # Validate data structure
        sample = records[0]
        required_fields = ["date", "time", "price", "provider"]
        missing_fields = [field for field in required_fields if field not in sample]
        
        if missing_fields:
            log_test("Parser Functionality", False, f"Missing fields: {missing_fields}")
            return False
        
        details = f"Extracted: {extracted} records, Available: {len(records)} records"
        log_test("Parser Functionality", True, details)
        return True
        
    except Exception as e:
        log_test("Parser Functionality", False, f"Exception: {str(e)}")
        return False

def test_data_quality():
    """Test 4: Data Quality Validation"""
    try:
        # Get current data
        response = requests.get(f"{BASE_URL}/api/booking-data", timeout=10)
        
        if response.status_code != 200:
            log_test("Data Quality", False, f"Cannot access data: HTTP {response.status_code}")
            return False
        
        data = response.json()
        records = data.get("data", [])
        
        if not records:
            log_test("Data Quality", False, "No data to validate")
            return False
        
        # Validate sample record
        sample = records[0]
        issues = []
        
        # Check date format
        date_val = sample.get("date", "")
        if not date_val or len(date_val) != 10:
            issues.append("Invalid date format")
        
        # Check time format  
        time_val = sample.get("time", "")
        if not time_val or ":" not in time_val:
            issues.append("Invalid time format")
        
        # Check price
        price_val = sample.get("price", "")
        if not price_val or "₽" not in price_val:
            issues.append("Invalid price format")
        
        # Check provider
        provider_val = sample.get("provider", "")
        if not provider_val or len(provider_val.strip()) == 0:
            issues.append("Empty provider")
        
        if issues:
            log_test("Data Quality", False, f"Issues: {', '.join(issues)}")
            return False
        
        details = f"Sample: {date_val} {time_val}, {price_val}, {provider_val}"
        log_test("Data Quality", True, details)
        return True
        
    except Exception as e:
        log_test("Data Quality", False, f"Exception: {str(e)}")
        return False

def test_configuration():
    """Test 5: Configuration Verification"""
    try:
        # Check URLs configuration
        response = requests.get(f"{BASE_URL}/api/urls", timeout=10)
        
        if response.status_code != 200:
            log_test("Configuration", False, f"Cannot access config: HTTP {response.status_code}")
            return False
        
        config = response.json()
        urls = config.get("urls", [])
        count = config.get("count", 0)
        
        if count == 0:
            log_test("Configuration", False, "No URLs configured", ">0 URLs", "0 URLs")
            return False
        
        # Check parser status
        status_response = requests.get(f"{BASE_URL}/parser/status", timeout=10)
        if status_response.status_code != 200:
            log_test("Configuration", False, f"Cannot access parser status: HTTP {status_response.status_code}")
            return False
        
        status_data = status_response.json()
        ready = status_data.get("ready", False)
        
        if not ready:
            log_test("Configuration", False, "Parser not ready", "True", "False")
            return False
        
        details = f"URLs: {count}, Ready: {ready}"
        log_test("Configuration", True, details)
        return True
        
    except Exception as e:
        log_test("Configuration", False, f"Exception: {str(e)}")
        return False

def generate_demo_report():
    """Generate demo report"""
    
    # Get current system status
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=10).json()
        parser_status = requests.get(f"{BASE_URL}/parser/status", timeout=10).json()
        booking_data = requests.get(f"{BASE_URL}/api/booking-data?limit=3", timeout=10).json()
        
        report = {
            "demo_report": {
                "timestamp": datetime.now().isoformat(),
                "test_summary": {
                    "total_tests": RESULTS["total"],
                    "passed": RESULTS["passed"],
                    "failed": RESULTS["failed"],
                    "success_rate": f"{(RESULTS['passed']/RESULTS['total']*100):.1f}%" if RESULTS["total"] > 0 else "0%"
                },
                "system_status": {
                    "version": health.get("version", "Unknown"),
                    "production_ready": health.get("production_ready", False),
                    "parsing_method": health.get("parsing_method", "Unknown"),
                    "browser_dependencies": health.get("browser_dependencies", "Unknown")
                },
                "parser_info": {
                    "urls_configured": parser_status.get("configuration", {}).get("url_count", 0),
                    "total_extracted": parser_status.get("statistics", {}).get("total_extracted", 0),
                    "last_run": parser_status.get("statistics", {}).get("last_run", "Never")
                },
                "sample_data": booking_data.get("data", [])[:3],
                "test_details": TESTS
            }
        }
        
        # Save report
        with open("demo_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report
        
    except Exception as e:
        print(f"❌ Could not generate full report: {e}")
        return {"error": str(e)}

def main():
    """Main demo execution"""
    print("🎯 YCLIENTS PARSER - AUTOMATED DEMO")
    print("=" * 50)
    print(f"🌐 Testing System: {BASE_URL}")
    print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all tests
    test_system_health()
    test_api_endpoints()
    test_parser_functionality()
    test_data_quality()
    test_configuration()
    
    # Summary
    print("=" * 50)
    print("📊 DEMO RESULTS SUMMARY")
    print("=" * 50)
    
    success_rate = (RESULTS["passed"] / RESULTS["total"] * 100) if RESULTS["total"] > 0 else 0
    
    print(f"✅ Tests Passed: {RESULTS['passed']}")
    print(f"❌ Tests Failed: {RESULTS['failed']}")
    print(f"📊 Total Tests: {RESULTS['total']}")
    print(f"🎯 Success Rate: {success_rate:.1f}%")
    print()
    
    if RESULTS["failed"] == 0:
        print("🎉 ALL TESTS PASSED! System is production ready!")
        print("✅ Parser is fully functional and extracting real data")
        print("✅ All APIs working correctly")
        print("✅ Data quality meets requirements")
        print("✅ Configuration is valid")
    else:
        print("⚠️ Some tests failed. Please review results above.")
    
    # Generate detailed report
    print("\n📋 Generating detailed demo report...")
    report = generate_demo_report()
    
    if "error" not in report:
        print("✅ Demo report saved to: demo_report.json")
        
        # Show sample data
        sample_data = report.get("demo_report", {}).get("sample_data", [])
        if sample_data:
            print("\n📝 SAMPLE EXTRACTED DATA:")
            for i, record in enumerate(sample_data[:2], 1):
                print(f"   Record {i}:")
                print(f"     Date: {record.get('date', 'N/A')}")
                print(f"     Time: {record.get('time', 'N/A')}")
                print(f"     Price: {record.get('price', 'N/A')}")
                print(f"     Provider: {record.get('provider', 'N/A')}")
                print(f"     Location: {record.get('location_name', 'N/A')}")
    
    print(f"\n⏰ Demo Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔗 System URLs for client review:")
    print(f"   📊 Dashboard: {BASE_URL}")
    print(f"   ❤️ Health: {BASE_URL}/health")
    print(f"   🗃️ Data API: {BASE_URL}/api/booking-data")
    print(f"   📚 Docs: {BASE_URL}/docs")
    
    return RESULTS["failed"] == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
