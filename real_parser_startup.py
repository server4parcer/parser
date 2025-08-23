#!/usr/bin/env python3
"""
REAL PARSER - Extracts actual data from YClients and saves to Supabase
"""
import os
import asyncio
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re
from fastapi import FastAPI
import uvicorn

# Supabase integration
from supabase import create_client

print("🚀 REAL YCLIENTS PARSER STARTUP")

# Environment variables
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')  
PARSE_URLS = os.environ.get('PARSE_URLS', '').split(',')

print(f"✅ Supabase URL: {SUPABASE_URL[:30]}...")
print(f"✅ Parse URLs: {len(PARSE_URLS)} venues configured")

# Initialize Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

app = FastAPI(title="YClients Parser - Real Data")

def parse_yclients_venue(url):
    """Extract real booking data from YClients venue page"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"🔍 Parsing: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract venue name from URL or page
        venue_name = extract_venue_name(url, soup)
        
        # Look for booking elements with real selectors
        bookings = []
        
        # Try multiple YClients selectors for time slots
        time_selectors = [
            '.time-slot', '.booking-time', '.available-time',
            '[data-time]', '.schedule-item', '.time-cell'
        ]
        
        price_selectors = [
            '.price', '.cost', '[data-price]', '.booking-price'
        ]
        
        # Extract times and prices
        times = []
        prices = []
        
        for selector in time_selectors:
            elements = soup.select(selector)
            for el in elements:
                time_text = el.get_text(strip=True)
                if re.match(r'\d{1,2}:\d{2}', time_text):
                    times.append(time_text)
        
        for selector in price_selectors:
            elements = soup.select(selector)
            for el in elements:
                price_text = el.get_text(strip=True)
                if '₽' in price_text or 'руб' in price_text:
                    # Clean price: "6,000 ₽" -> "6000"
                    clean_price = re.sub(r'[^\d]', '', price_text)
                    if clean_price:
                        prices.append(f"{clean_price} ₽")
        
        # Create booking entries
        for i, time_slot in enumerate(times[:10]):  # Limit to 10 results
            price = prices[i] if i < len(prices) else "Цена не указана"
            
            booking = {
                "venue_name": venue_name,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": time_slot,
                "price": price,
                "duration": 60,  # Default 1 hour
                "court_name": f"Площадка {i+1}",
                "extracted_at": datetime.now().isoformat(),
                "source_url": url
            }
            bookings.append(booking)
            
        print(f"✅ Extracted {len(bookings)} bookings from {venue_name}")
        return bookings
        
    except Exception as e:
        print(f"❌ Error parsing {url}: {e}")
        return []

def extract_venue_name(url, soup):
    """Extract venue name from URL or page content"""
    # Try to get from page title first
    title = soup.find('title')
    if title:
        title_text = title.get_text()
        if 'yclients' not in title_text.lower():
            return title_text[:50]
    
    # Extract from URL pattern
    if 'company/' in url:
        company_id = url.split('company/')[1].split('/')[0]
        return f"Venue_{company_id}"
    
    return "YClients_Venue"

def save_to_supabase(bookings):
    """Save booking data to Supabase"""
    if not supabase or not bookings:
        return 0
        
    try:
        # Insert data into booking_data table
        result = supabase.table('booking_data').insert(bookings).execute()
        return len(bookings)
    except Exception as e:
        print(f"❌ Supabase error: {e}")
        return 0

last_parse_result = {"extracted": 0, "timestamp": "never"}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "version": "real_parser",
        "supabase_connected": supabase is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/parser/status")
def parser_status():
    return {
        "status": "ready_to_work",
        "mode": "real_parsing",
        "last_run": last_parse_result["timestamp"],
        "last_extracted": last_parse_result["extracted"],
        "urls_configured": len([u for u in PARSE_URLS if u.strip()]),
        "supabase_connected": supabase is not None
    }

@app.get("/parser/run")
def parser_run():
    """Run real YClients parsing"""
    global last_parse_result
    
    if not PARSE_URLS or not supabase:
        return {
            "status": "error",
            "message": "Missing configuration",
            "supabase": supabase is not None,
            "urls": len(PARSE_URLS)
        }
    
    all_bookings = []
    
    for url in PARSE_URLS:
        if url.strip():
            venue_bookings = parse_yclients_venue(url.strip())
            all_bookings.extend(venue_bookings)
    
    # Save to Supabase
    saved_count = save_to_supabase(all_bookings)
    
    last_parse_result = {
        "extracted": len(all_bookings),
        "saved": saved_count, 
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "status": "success",
        "extracted": len(all_bookings),
        "saved_to_supabase": saved_count,
        "venues_parsed": len([u for u in PARSE_URLS if u.strip()]),
        "message": f"🎉 УСПЕХ! Извлечено {len(all_bookings)} записей с реальных площадок"
    }

@app.get("/api/booking-data")
def get_booking_data():
    """Get booking data from Supabase"""
    if not supabase:
        return {"error": "Supabase not configured"}
    
    try:
        result = supabase.table('booking_data').select("*").limit(50).execute()
        return {
            "data": result.data,
            "count": len(result.data),
            "message": "Реальные данные из Supabase"
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("✅ Starting REAL YClients parser...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")