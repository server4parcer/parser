#!/usr/bin/env python3
"""Simple HTML fetcher for YClients - no browser needed"""

import requests
import json
from bs4 import BeautifulSoup

url = "https://n1165596.yclients.com/company/1109937/record-type?o="

print(f"Fetching: {url}")
response = requests.get(url, headers={
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
})

print(f"Status: {response.status_code}")

with open("/tmp/yclients_page.html", "w", encoding="utf-8") as f:
    f.write(response.text)

print("Saved to /tmp/yclients_page.html")

# Parse and analyze
soup = BeautifulSoup(response.text, 'html.parser')

print("\n" + "="*80)
print("ANALYZING HTML STRUCTURE")
print("="*80)

# Find all elements with 'time', 'slot', 'booking' in class
keywords = ['time', 'slot', 'booking', 'schedule', 'price', 'cost', 'staff', 'master']

for keyword in keywords:
    elements = soup.find_all(class_=lambda x: x and keyword in x.lower())
    if elements:
        print(f"\n🔍 Elements with '{keyword}' in class: {len(elements)}")
        for elem in elements[:3]:
            print(f"   <{elem.name} class='{elem.get('class')}'>{elem.get_text().strip()[:50]}")

# Find all data-* attributes
print("\n🔍 Elements with data-price attribute:")
price_data = soup.find_all(attrs={"data-price": True})
print(f"   Found: {len(price_data)}")

print("\n🔍 Elements with data-time attribute:")
time_data = soup.find_all(attrs={"data-time": True})
print(f"   Found: {len(time_data)}")

print("\n🔍 Elements with data-staff attribute:")
staff_data = soup.find_all(attrs={"data-staff": True})
print(f"   Found: {len(staff_data)}")

# Search for currency symbols
print("\n💰 Elements containing '₽':")
ruble_elements = soup.find_all(string=lambda x: x and '₽' in x)
print(f"   Found: {len(ruble_elements)}")
for elem in ruble_elements[:5]:
    parent = elem.parent
    print(f"   <{parent.name} class='{parent.get('class')}'>{str(elem).strip()[:50]}")

print("\nAnalysis complete! Check /tmp/yclients_page.html for full HTML")
