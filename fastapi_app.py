#!/usr/bin/env python3
"""
STEP 2: FastAPI upgrade from Hello World
- Maintains working Hello World structure
- Adds proper /health and API endpoints  
- Uses environment variables from Step 1
"""
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

# Get environment variables (with fallbacks)
API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("API_PORT", "8000"))
API_KEY = os.environ.get("API_KEY", "default_key")
PARSE_URLS = os.environ.get("PARSE_URLS", "")

# Create FastAPI app
app = FastAPI(
    title="YClients Parser API",
    description="Step 2: FastAPI upgrade from Hello World",
    version="2.0.0"
)

@app.get("/")
def read_root():
    """Root endpoint - shows we're upgraded to FastAPI"""
    return HTMLResponse("""
    <h1>🎉 FastAPI Upgrade Success!</h1>
    <p><strong>Step 2 Complete:</strong> FastAPI is working</p>
    <p><strong>Environment Variables:</strong></p>
    <ul>
        <li>API_HOST: {}</li>
        <li>API_PORT: {}</li>
        <li>API_KEY: {}***</li>
        <li>PARSE_URLS: {}</li>
    </ul>
    <p><strong>Available Endpoints:</strong></p>
    <ul>
        <li><a href="/health">/health</a> - Health check</li>
        <li><a href="/docs">/docs</a> - API documentation</li>
        <li><a href="/status">/status</a> - System status</li>
    </ul>
    """.format(API_HOST, API_PORT, API_KEY[:8], PARSE_URLS[:50] + "..." if len(PARSE_URLS) > 50 else PARSE_URLS))

@app.get("/health")
def health_check():
    """Health endpoint for monitoring"""
    return {
        "status": "ok",
        "step": 2,
        "message": "FastAPI upgrade successful",
        "environment": {
            "api_host": API_HOST,
            "api_port": API_PORT,
            "has_api_key": bool(API_KEY),
            "has_parse_urls": bool(PARSE_URLS),
            "parse_urls_count": len(PARSE_URLS.split(",")) if PARSE_URLS else 0
        }
    }

@app.get("/status")
def get_status():
    """System status endpoint"""
    return {
        "service": "yclients-parser",
        "version": "2.0.0",
        "step": "2 - FastAPI Upgrade",
        "next_step": "3 - Database Connection",
        "configuration": {
            "api_host": API_HOST,
            "api_port": API_PORT,
            "api_key_configured": bool(API_KEY),
            "parse_urls_configured": bool(PARSE_URLS),
            "urls_to_parse": PARSE_URLS.split(",") if PARSE_URLS else []
        }
    }

if __name__ == "__main__":
    print(f"🚀 STEP 2: Starting FastAPI server on {API_HOST}:{API_PORT}")
    print(f"📋 Environment check:")
    print(f"   - API_KEY: {'✅ Set' if API_KEY else '❌ Missing'}")
    print(f"   - PARSE_URLS: {'✅ Set' if PARSE_URLS else '❌ Missing'}")
    print(f"   - URLs to parse: {len(PARSE_URLS.split(',')) if PARSE_URLS else 0}")
    
    uvicorn.run(
        app, 
        host=API_HOST, 
        port=API_PORT,
        log_level="info"
    )
