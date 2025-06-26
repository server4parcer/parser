#!/usr/bin/env python3
"""
SUPER SIMPLE startup - bypass all complexity and just start the app
"""
import os
import sys
import asyncio

print("=" * 50)
print("🚀 SUPER SIMPLE STARTUP")
print("=" * 50)

# Check basic environment
required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'API_HOST', 'API_PORT']
missing = [var for var in required_vars if not os.environ.get(var)]

if missing:
    print(f"❌ MISSING: {missing}")
    sys.exit(1)

print("✅ Required environment variables present")

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'src'))

# Set default command line args to avoid parsing issues
sys.argv = ['main.py', '--mode', 'all']

# Basic environment setup
os.environ.setdefault('API_HOST', '0.0.0.0')
os.environ.setdefault('API_PORT', '8000')
os.environ.setdefault('API_DEBUG', 'false')
os.environ.setdefault('PARSE_INTERVAL', '600')

print("🎯 Attempting to import and run src.main...")

try:
    # Import main module
    import src.main
    print("✅ src.main imported successfully")
    
    # Run the async main function
    print("🚀 Starting asyncio.run(main())...")
    asyncio.run(src.main.main())
    
except Exception as e:
    print(f"💥 ERROR: {e}")
    import traceback
    traceback.print_exc()
    
    # Try alternative approach
    print("\n🔄 Trying alternative import...")
    try:
        sys.path.append('/app')
        sys.path.append('/app/src')
        
        # Try direct file execution
        import importlib.util
        spec = importlib.util.spec_from_file_location("main", "/app/src/main.py")
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)
        
        print("🚀 Starting via importlib...")
        asyncio.run(main_module.main())
        
    except Exception as e2:
        print(f"💥 Alternative also failed: {e2}")
        traceback.print_exc()
        sys.exit(1)
