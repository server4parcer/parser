#!/usr/bin/env python3
"""
Test script for Pavel's YClients URL parsing
Tests the new lightweight parser with his specific URL
"""
import asyncio
import sys
import os
import json
from datetime import datetime

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.parser.lightweight_yclients_parser import LightweightYClientsParser
from src.parser.parser_router import ParserRouter

# Pavel's test URL
PAVEL_URL = "https://b918666.yclients.com/company/855029/personal/menu?o=m-1"

async def test_pavel_parser():
    """Test the parser with Pavel's specific URL."""
    print("🧪 TESTING PAVEL'S YCLIENTS PARSER")
    print("=" * 50)
    print(f"URL: {PAVEL_URL}")
    print()
    
    # Test 1: Direct lightweight parser
    print("📋 Test 1: Direct Lightweight YClients Parser")
    print("-" * 40)
    
    parser = LightweightYClientsParser()
    
    try:
        results = parser.parse_url(PAVEL_URL)
        
        print(f"✅ Parser executed successfully")
        print(f"📊 Results: {len(results)} records extracted")
        print()
        
        if results:
            print("📋 EXTRACTED DATA:")
            for i, record in enumerate(results, 1):
                print(f"\n🎯 Record {i}:")
                print(f"   Venue: {record.get('venue_name', 'N/A')}")
                print(f"   Date: {record.get('date', 'N/A')}")
                print(f"   Time: {record.get('time', 'N/A')}")
                print(f"   Price: {record.get('price', 'N/A')}")
                print(f"   Duration: {record.get('duration', 'N/A')} minutes")
                print(f"   Court Type: {record.get('court_type', 'N/A')}")
                print(f"   Service: {record.get('service_name', 'N/A')}")
        else:
            print("❌ No data extracted")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    
    # Test 2: Parser Router (what lightweight_parser.py uses)
    print("📋 Test 2: Parser Router (Production Path)")
    print("-" * 40)
    
    try:
        # Mock database manager for testing
        class MockDBManager:
            def __init__(self):
                self.is_initialized = True
        
        router = ParserRouter(MockDBManager())
        
        router_results = await router.parse_url(PAVEL_URL)
        
        print(f"✅ Router executed successfully")
        print(f"📊 Results: {len(router_results)} records extracted")
        print()
        
        if router_results:
            print("📋 ROUTER EXTRACTED DATA:")
            for i, record in enumerate(router_results, 1):
                print(f"\n🎯 Record {i}:")
                print(f"   Venue: {record.get('venue_name', 'N/A')}")
                print(f"   Date: {record.get('date', 'N/A')}")
                print(f"   Time: {record.get('time', 'N/A')}")
                print(f"   Price: {record.get('price', 'N/A')}")
                print(f"   Duration: {record.get('duration', 'N/A')} minutes")
        else:
            print("❌ No data extracted via router")
            
    except Exception as e:
        print(f"❌ Router Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🎯 TEST COMPLETE")
    
    # Save results to file for analysis
    if results or router_results:
        test_results = {
            "test_date": datetime.now().isoformat(),
            "url_tested": PAVEL_URL,
            "direct_parser_results": results,
            "router_results": router_results,
            "total_records": len(results) + len(router_results)
        }
        
        with open("pavel_parser_test_results.json", "w", encoding="utf-8") as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        
        print(f"📁 Results saved to: pavel_parser_test_results.json")

if __name__ == "__main__":
    asyncio.run(test_pavel_parser())