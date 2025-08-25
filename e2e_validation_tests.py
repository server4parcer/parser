#!/usr/bin/env python3
"""
🧪 END-TO-END VALIDATION TESTS
Complete system validation for Pavel's YClients Parser
Tests the entire flow: Parsing → Saving → API → Scheduling
"""
import requests
import json
import time
from datetime import datetime, timedelta
import asyncio
from supabase import create_client
import os

BASE_URL = "https://server4parcer-parser-4949.twc1.net"
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://axedyenlcdfrjhwfcokj.supabase.co')  # Example URL
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'your-key-here')  # User should set this

class E2EValidator:
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        
    def log_test(self, test_name, status, details="", data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,  # "PASS", "FAIL", "SKIP"
            "details": details,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        # Print result
        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️"
        print(f"{emoji} {test_name}: {details}")
        if data:
            print(f"   📊 Data: {json.dumps(data, indent=2)[:200]}...")
    
    def test_system_health(self):
        """Test 1: System health and configuration"""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                
                # Validate expected health response
                expected_fields = ["status", "parser_type", "supabase_connected"]
                if all(field in health_data for field in expected_fields):
                    if health_data["parser_type"] == "hybrid_realistic":
                        self.log_test("System Health Check", "PASS", 
                                    f"System healthy, parser type: {health_data['parser_type']}", health_data)
                    else:
                        self.log_test("System Health Check", "FAIL", 
                                    f"Wrong parser type: {health_data.get('parser_type', 'unknown')}", health_data)
                else:
                    self.log_test("System Health Check", "FAIL", "Missing health fields", health_data)
            else:
                self.log_test("System Health Check", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("System Health Check", "FAIL", f"Connection error: {str(e)}")
    
    def test_parser_configuration(self):
        """Test 2: Parser configuration validation"""
        try:
            response = requests.get(f"{BASE_URL}/parser/status", timeout=10)
            if response.status_code == 200:
                config_data = response.json()
                
                urls_configured = config_data.get("urls_configured", 0)
                if urls_configured >= 6:
                    self.log_test("Parser Configuration", "PASS", 
                                f"{urls_configured} venues configured", config_data)
                else:
                    self.log_test("Parser Configuration", "FAIL", 
                                f"Only {urls_configured} venues configured, expected 6", config_data)
            else:
                self.log_test("Parser Configuration", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Parser Configuration", "FAIL", f"Error: {str(e)}")
    
    def test_supabase_connection(self):
        """Test 3: Supabase database connection"""
        try:
            response = requests.get(f"{BASE_URL}/debug/supabase", timeout=15)
            if response.status_code == 200:
                debug_data = response.json()
                
                # Check if both tests passed
                tests = debug_data.get("tests", [])
                passed_tests = [t for t in tests if t.get("status") == "success"]
                
                if len(passed_tests) == 2:
                    self.log_test("Supabase Connection", "PASS", 
                                f"All {len(passed_tests)} connection tests passed", debug_data)
                else:
                    failed_tests = [t for t in tests if t.get("status") != "success"]
                    self.log_test("Supabase Connection", "FAIL", 
                                f"{len(failed_tests)} tests failed", debug_data)
            else:
                self.log_test("Supabase Connection", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Supabase Connection", "FAIL", f"Error: {str(e)}")
    
    def test_data_extraction_and_saving(self):
        """Test 4: Full data extraction and saving flow"""
        try:
            print("🔄 Running full parsing test (may take 30-60 seconds)...")
            response = requests.get(f"{BASE_URL}/parser/run", timeout=120)
            
            if response.status_code == 200:
                parse_data = response.json()
                
                extracted = parse_data.get("extracted", 0)
                saved = parse_data.get("saved_to_supabase", 0)
                venues_parsed = parse_data.get("venues_parsed", 0)
                
                # Validate results
                if extracted > 0 and saved > 0 and venues_parsed >= 6:
                    if extracted == saved:
                        self.log_test("Data Extraction & Saving", "PASS", 
                                    f"Extracted {extracted}, saved {saved}, parsed {venues_parsed} venues", parse_data)
                    else:
                        self.log_test("Data Extraction & Saving", "FAIL", 
                                    f"Data loss: extracted {extracted}, saved {saved}", parse_data)
                else:
                    self.log_test("Data Extraction & Saving", "FAIL", 
                                f"Low results: extracted {extracted}, saved {saved}", parse_data)
            else:
                self.log_test("Data Extraction & Saving", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Data Extraction & Saving", "FAIL", f"Error: {str(e)}")
    
    def test_data_quality(self):
        """Test 5: Data quality validation"""
        if not SUPABASE_URL or not SUPABASE_KEY or SUPABASE_KEY == 'your-key-here':
            self.log_test("Data Quality Check", "SKIP", "Supabase credentials not provided")
            return
            
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # Get recent records
            result = supabase.table('booking_data').select("*").order('created_at.desc').limit(10).execute()
            
            if result.data:
                records = result.data
                quality_issues = []
                
                for record in records:
                    # Check date is future (not old demo data)
                    try:
                        booking_date = datetime.strptime(record['date'], '%Y-%m-%d').date()
                        today = datetime.now().date()
                        if booking_date < today:
                            quality_issues.append(f"Past date found: {record['date']}")
                    except:
                        quality_issues.append(f"Invalid date format: {record['date']}")
                    
                    # Check price format
                    price = record.get('price', '')
                    if 'TEST' in price.upper() or 'DEBUG' in price.upper():
                        quality_issues.append(f"Test data found: {price}")
                    
                    # Check venue name
                    venue = record.get('venue_name', '')
                    if 'TEST' in venue.upper() or venue == 'Unknown':
                        quality_issues.append(f"Test venue found: {venue}")
                
                if not quality_issues:
                    self.log_test("Data Quality Check", "PASS", 
                                f"Validated {len(records)} records - all high quality", 
                                {"sample_records": records[:3]})
                else:
                    self.log_test("Data Quality Check", "FAIL", 
                                f"Quality issues found: {quality_issues[:3]}", 
                                {"issues": quality_issues})
            else:
                self.log_test("Data Quality Check", "FAIL", "No data found in Supabase")
                
        except Exception as e:
            self.log_test("Data Quality Check", "FAIL", f"Supabase error: {str(e)}")
    
    def test_time_consistency(self):
        """Test 6: Time and scheduling consistency"""
        try:
            # Run parser twice with a small interval to check consistency
            print("🔄 Testing parsing consistency...")
            
            response1 = requests.get(f"{BASE_URL}/parser/run", timeout=120)
            time.sleep(5)  # Wait 5 seconds
            response2 = requests.get(f"{BASE_URL}/parser/run", timeout=120)
            
            if response1.status_code == 200 and response2.status_code == 200:
                data1 = response1.json()
                data2 = response2.json()
                
                extracted1 = data1.get("extracted", 0)
                extracted2 = data2.get("extracted", 0)
                
                # Results should be similar (allowing some variation)
                if abs(extracted1 - extracted2) <= 5:  # Allow 5 record difference
                    self.log_test("Parsing Consistency", "PASS", 
                                f"Consistent results: run1={extracted1}, run2={extracted2}")
                else:
                    self.log_test("Parsing Consistency", "FAIL", 
                                f"Inconsistent results: run1={extracted1}, run2={extracted2}")
            else:
                self.log_test("Parsing Consistency", "FAIL", "One or both requests failed")
                
        except Exception as e:
            self.log_test("Parsing Consistency", "FAIL", f"Error: {str(e)}")
    
    def test_performance_benchmarks(self):
        """Test 7: Performance and response time validation"""
        performance_tests = [
            ("Health Check", f"{BASE_URL}/health", 5),
            ("Parser Status", f"{BASE_URL}/parser/status", 10),
            ("Supabase Debug", f"{BASE_URL}/debug/supabase", 20),
        ]
        
        passed_benchmarks = 0
        for test_name, endpoint, max_time in performance_tests:
            try:
                start = time.time()
                response = requests.get(endpoint, timeout=max_time)
                duration = time.time() - start
                
                if response.status_code == 200 and duration <= max_time:
                    self.log_test(f"Performance - {test_name}", "PASS", 
                                f"Responded in {duration:.2f}s (limit: {max_time}s)")
                    passed_benchmarks += 1
                else:
                    self.log_test(f"Performance - {test_name}", "FAIL", 
                                f"Too slow: {duration:.2f}s or HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"Performance - {test_name}", "FAIL", f"Error: {str(e)}")
        
        # Overall performance score
        if passed_benchmarks == len(performance_tests):
            self.log_test("Overall Performance", "PASS", f"All {passed_benchmarks} benchmarks passed")
        else:
            self.log_test("Overall Performance", "FAIL", f"Only {passed_benchmarks}/{len(performance_tests)} benchmarks passed")
    
    def generate_report(self):
        """Generate final E2E test report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        skipped_tests = len([r for r in self.test_results if r["status"] == "SKIP"])
        
        duration = datetime.now() - self.start_time
        
        print("\n" + "="*60)
        print("🧪 END-TO-END VALIDATION REPORT")
        print("="*60)
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏭️ Skipped: {skipped_tests}")
        print(f"⏱️ Duration: {duration.total_seconds():.1f} seconds")
        print(f"🎯 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED - SYSTEM IS FULLY OPERATIONAL! 🎉")
        else:
            print(f"\n⚠️ {failed_tests} TESTS FAILED - REVIEW REQUIRED")
            
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status_emoji = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⏭️"
            print(f"{status_emoji} {result['test']}: {result['details']}")
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "skipped": skipped_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "duration_seconds": duration.total_seconds(),
            "all_passed": failed_tests == 0
        }

def run_e2e_tests():
    """Run all end-to-end tests"""
    print("🚀 STARTING END-TO-END VALIDATION TESTS")
    print("🎯 Testing Pavel's YClients Parser System")
    print("-" * 60)
    
    validator = E2EValidator()
    
    # Run all tests
    validator.test_system_health()
    validator.test_parser_configuration()
    validator.test_supabase_connection()
    validator.test_data_extraction_and_saving()
    validator.test_data_quality()
    validator.test_time_consistency()
    validator.test_performance_benchmarks()
    
    # Generate final report
    report = validator.generate_report()
    
    return report

if __name__ == "__main__":
    report = run_e2e_tests()
    
    # Exit with appropriate code
    exit(0 if report["all_passed"] else 1)