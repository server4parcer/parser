#!/usr/bin/env python3
"""
Simple startup script for TimeWeb debugging
"""
import os
import sys

def check_environment():
    """Check environment variables"""
    print("🔍 Checking environment variables...")
    
    required_vars = [
        'SUPABASE_URL', 'SUPABASE_KEY', 'API_HOST', 'API_PORT'
    ]
    
    missing = []
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing.append(var)
        else:
            print(f"✅ {var}: {'*' * min(10, len(value))}...")
    
    if missing:
        print(f"❌ Missing variables: {missing}")
        return False
    
    print("✅ All required environment variables present")
    return True

def main():
    """Main startup function"""
    print("🚀 YClients Parser starting...")
    
    # Check environment
    if not check_environment():
        print("💥 Environment check failed!")
        sys.exit(1)
    
    # Add paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)
    sys.path.insert(0, current_dir)
    
    try:
        print("📦 Importing modules...")
        from src.main import main as app_main
        print("✅ Modules imported successfully")
        
        print("🎯 Starting application...")
        app_main()
        
    except Exception as e:
        print(f"💥 Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
