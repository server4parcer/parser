#!/usr/bin/env python3
"""
Test full system integration with Pavel's URL
"""
import asyncio
import sys
import os
import requests
import json
from datetime import datetime

# Test the complete system as it would run in production
PAVEL_URL = "https://b918666.yclients.com/company/855029/personal/menu?o=m-1"

async def test_run_parser():
    """Test the run_parser function directly."""
    print("🧪 TESTING FULL SYSTEM WITH PAVEL'S URL")
    print("=" * 50)
    
    # Set up environment like TimeWeb would
    os.environ['PARSE_URLS'] = PAVEL_URL
    os.environ['SUPABASE_URL'] = 'https://axedyenlcdfrjhwfcokj.supabase.co'
    os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF4ZWR5ZW5sY2RmcmpoZmNva2oiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTcxNzczMjU3NSwiZXhwIjoyMDMzMzA4NTc1fQ.xQrNXHJt5N3DgQzN8rOGP3qOz1c-LL-7dV7ZgAQe3d0'
    os.environ['API_HOST'] = '0.0.0.0'
    os.environ['API_PORT'] = '8000'
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    # Import and test the run_parser function
    from lightweight_parser import run_parser
    
    try:
        print(f"🎯 Testing with URL: {PAVEL_URL}")
        print(f"🗄️  Using Supabase: {os.environ['SUPABASE_URL'][:30]}...")
        print()
        
        result = await run_parser()
        
        print("📊 PARSER RESULT:")
        print(f"   Status: {result.get('status')}")
        print(f"   Extracted: {result.get('extracted', 0)} records")
        print(f"   Message: {result.get('message', 'Success')}")
        
        if result.get('status') == 'success':
            print("\n✅ PARSER TEST SUCCESSFUL!")
            print("🎉 Data should now be in Supabase database")
        else:
            print(f"\n❌ PARSER TEST FAILED: {result}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

def test_api_endpoints():
    """Test API endpoints as they would be called in production."""
    print("\n" + "=" * 50)
    print("🌐 TESTING API ENDPOINTS")
    print("=" * 50)
    
    # Note: These would need the server running to work
    # For now just test the functions directly
    
    try:
        from lightweight_parser import app, parse_results, get_parser_status
        
        print("📋 Testing get_parser_status()...")
        status = get_parser_status()
        print(f"   Parser ready: {status.get('ready')}")
        print(f"   URL count: {status.get('configuration', {}).get('url_count', 0)}")
        print(f"   Method: {status.get('parsing_method')}")
        
        print("\n📊 Testing parse_results...")
        print(f"   Total extracted: {parse_results.get('total_extracted', 0)}")
        print(f"   Status: {parse_results.get('status', 'unknown')}")
        print(f"   Supabase active: {parse_results.get('supabase_active', False)}")
        
        print("\n✅ API TESTS COMPLETED")
        
    except Exception as e:
        print(f"❌ API TEST ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_run_parser())
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("🎯 FULL SYSTEM TEST COMPLETE")
    print("📋 Next steps for Pavel:")
    print("   1. Deploy this code to TimeWeb")
    print("   2. Set environment variables in TimeWeb panel")
    print("   3. Check /parser/run endpoint")
    print("   4. Verify data in Supabase dashboard")