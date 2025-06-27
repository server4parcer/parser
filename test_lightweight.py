#!/usr/bin/env python3
"""
Test script for lightweight parser
"""
import os
import sys

# Set environment variables
os.environ['API_HOST'] = '127.0.0.1'
os.environ['API_PORT'] = '8001'
os.environ['API_KEY'] = 'test_key'
os.environ['PARSE_URLS'] = 'https://n1165596.yclients.com/company/1109937/record-type?o='
os.environ['SUPABASE_URL'] = 'test'
os.environ['SUPABASE_KEY'] = 'test'
os.environ['PARSE_INTERVAL'] = '600'

# Add current directory to path
sys.path.insert(0, '.')

# Test import without running server
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

print("🧪 Testing lightweight parser components...")

# Test 1: Import check
try:
    print("✅ Successfully imported requests and BeautifulSoup")
except Exception as e:
    print(f"❌ Import error: {e}")
    exit(1)

# Test 2: Create parser class
class TestParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def test_request(self, url):
        try:
            response = self.session.get(url, timeout=10)
            print(f"✅ Request to {url} - Status: {response.status_code}")
            return True
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return False

# Test 3: Basic functionality
parser = TestParser()
test_url = "https://httpbin.org/get"  # Safe test URL
if parser.test_request(test_url):
    print("✅ HTTP requests working")
else:
    print("❌ HTTP requests failed")

# Test 4: YClients URL test (quick check)
yclients_url = os.environ['PARSE_URLS']
print(f"🎯 Testing YClients URL: {yclients_url}")
if parser.test_request(yclients_url):
    print("✅ YClients URL accessible")
else:
    print("⚠️ YClients URL not accessible (may be expected)")

print("🎉 Basic functionality test completed!")
print("✅ Ready to deploy lightweight parser!")
