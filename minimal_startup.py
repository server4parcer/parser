#!/usr/bin/env python3
"""
MINIMAL startup - Just FastAPI server with basic endpoints, no complex imports
"""
import os
from datetime import datetime
from fastapi import FastAPI
import uvicorn

print("🚀 MINIMAL PARSER STARTUP")

app = FastAPI(title="YClients Parser - Minimal")

@app.get("/health")
def health():
    return {
        "status": "healthy", 
        "version": "minimal",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/parser/status")
def parser_status():
    return {
        "status": "ready_to_work",
        "status_ru": "готов к работе", 
        "mode": "minimal",
        "last_run": "never_started",
        "last_run_ru": "не запускался",
        "urls_configured": len(os.environ.get("PARSE_URLS", "").split(","))
    }

@app.get("/parser/run")
def parser_run():
    return {
        "status": "success",
        "message": "Минимальная версия - только тестовые endpoints",
        "extracted": 0,
        "note": "Для полного парсинга нужна интеграция с Playwright"
    }

@app.get("/api/booking-data")
def get_booking_data():
    return {
        "data": [],
        "count": 0,
        "message": "Минимальная версия - нет данных"
    }

if __name__ == "__main__":
    print("✅ Starting minimal FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
