#!/usr/bin/env python3
"""
PLAYWRIGHT YCLIENTS PARSER - Real JavaScript parsing with 4-step navigation
Uses proper Playwright implementation for real YClients data extraction
"""
import os
import asyncio
import logging
from datetime import datetime
from fastapi import FastAPI
import uvicorn

# Import the proper Playwright-based parser - with fallback paths
try:
    from src.parser.yclients_parser import YClientsParser
    from src.database.db_manager import DatabaseManager
except ImportError:
    # Fallback for TimeWeb flat structure
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    from parser.yclients_parser import YClientsParser 
    from database.db_manager import DatabaseManager

# Supabase integration
from supabase import create_client

print("🚀 PLAYWRIGHT YCLIENTS PARSER STARTUP")

# Environment variables
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
PARSE_URLS = os.environ.get('PARSE_URLS', '').split(',')
API_HOST = os.environ.get('API_HOST', '0.0.0.0')
API_PORT = int(os.environ.get('API_PORT', 8000))

print(f"✅ Supabase URL: {SUPABASE_URL[:30] if SUPABASE_URL else 'Not set'}...")
print(f"✅ Parse URLs: {len([u for u in PARSE_URLS if u.strip()])} venues configured")

# Initialize components
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
db_manager = DatabaseManager() if supabase else None

app = FastAPI(title="YClients Playwright Parser")

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "parser_type": "playwright_browser",
        "javascript_support": True,
        "supabase_connected": supabase is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/parser/status")
async def parser_status():
    return {
        "status": "ready_for_real_parsing",
        "mode": "playwright_javascript",
        "urls_configured": len([u for u in PARSE_URLS if u.strip()]),
        "browser_automation": True,
        "supabase_connected": supabase is not None
    }

@app.get("/parser/run")
async def run_parser():
    """Run real YClients parsing with Playwright browser automation"""
    if not supabase:
        return {
            "status": "error",
            "message": "Supabase not configured"
        }
    
    active_urls = [url.strip() for url in PARSE_URLS if url.strip()]
    if not active_urls:
        return {
            "status": "error", 
            "message": "No PARSE_URLS configured"
        }
    
    try:
        print(f"🔍 Starting Playwright parsing for {len(active_urls)} venues...")
        
        # Initialize the proper Playwright parser
        parser = YClientsParser(active_urls, db_manager)
        
        # Run the parsing
        await parser.initialize()
        results = await parser.parse_all_urls()
        await parser.cleanup()
        
        # Save to Supabase
        saved_count = 0
        for venue_results in results:
            if venue_results:
                try:
                    # Convert to Supabase format
                    supabase_data = []
                    for booking in venue_results:
                        clean_booking = {
                            "venue_name": str(booking.get("venue_name", "Unknown")),
                            "date": str(booking.get("date", datetime.now().strftime("%Y-%m-%d"))),
                            "time": str(booking.get("time", "00:00")),
                            "price": str(booking.get("price", "Unknown")),
                            "duration": int(booking.get("duration", 60)),
                            "court_name": str(booking.get("court_name", "Court 1")),
                            "source_url": str(booking.get("source_url", ""))
                        }
                        supabase_data.append(clean_booking)
                    
                    if supabase_data:
                        result = supabase.table('booking_data').insert(supabase_data).execute()
                        saved_count += len(supabase_data)
                        
                except Exception as e:
                    print(f"❌ Error saving to Supabase: {e}")
        
        total_extracted = sum(len(r) for r in results if r)
        
        return {
            "status": "success",
            "extracted": total_extracted,
            "saved_to_supabase": saved_count,
            "venues_parsed": len([r for r in results if r]),
            "parser_type": "playwright_javascript",
            "message": f"🎉 УСПЕХ! Извлечено {total_extracted} записей с помощью Playwright"
        }
        
    except Exception as e:
        print(f"❌ Playwright parsing error: {e}")
        return {
            "status": "error",
            "message": f"Playwright parsing failed: {str(e)}"
        }

@app.get("/debug/supabase")
async def debug_supabase():
    """Debug Supabase connection"""
    if not supabase:
        return {"error": "Supabase not configured"}
    
    tests = []
    
    # Test 1: Table exists
    try:
        result = supabase.table('booking_data').select("*").limit(1).execute()
        tests.append({
            "test": "table_exists",
            "status": "success", 
            "existing_records": len(result.data) if result.data else 0
        })
    except Exception as e:
        tests.append({
            "test": "table_exists",
            "status": "failed",
            "error": str(e)
        })
    
    # Test 2: Simple insert
    try:
        test_data = [{
            "venue_name": "PLAYWRIGHT_TEST",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": "10:00",
            "price": "Test Playwright Parser",
            "duration": 60,
            "court_name": "Test Court",
            "source_url": "playwright_test"
        }]
        result = supabase.table('booking_data').insert(test_data).execute()
        tests.append({
            "test": "simple_insert",
            "status": "success",
            "inserted": len(test_data)
        })
    except Exception as e:
        tests.append({
            "test": "simple_insert", 
            "status": "failed",
            "error": str(e),
            "error_type": str(type(e))
        })
    
    return {"tests": tests}

if __name__ == "__main__":
    print("🎭 Starting Playwright YClients Parser...")
    print(f"🌐 Server: {API_HOST}:{API_PORT}")
    uvicorn.run(app, host=API_HOST, port=API_PORT)