#!/usr/bin/env python3
"""
DEBUG startup - diagnose TimeWeb startup issues
"""
import os
import sys

print("🔧 DEBUG STARTUP")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

# Check environment variables
required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'API_HOST', 'API_PORT']
for var in required_vars:
    value = os.environ.get(var, 'NOT SET')
    print(f"{var}: {value[:20]}..." if len(value) > 20 else f"{var}: {value}")

print("\n🔍 Testing imports...")

try:
    import fastapi
    print("✅ fastapi")
except Exception as e:
    print(f"❌ fastapi: {e}")

try:
    from src.database.db_manager import DatabaseManager
    print("✅ DatabaseManager")
except Exception as e:
    print(f"❌ DatabaseManager: {e}")

try:
    from settings import API_HOST
    print("✅ settings")
except Exception as e:
    print(f"❌ settings: {e}")

print("\n🚀 Starting basic FastAPI server...")

try:
    from fastapi import FastAPI
    import uvicorn
    
    app = FastAPI()
    
    @app.get("/health")
    def health():
        return {"status": "healthy", "debug": "startup_working"}
    
    print("✅ FastAPI app created")
    print("🎯 Starting server on 0.0.0.0:8000...")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
except Exception as e:
    print(f"💥 STARTUP ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)