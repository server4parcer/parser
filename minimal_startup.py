#!/usr/bin/env python3
"""
MINIMAL startup for debugging - just print and test basic stuff
"""
import os
import sys

# Print Python version and basic info
print("=" * 50)
print("🚀 MINIMAL STARTUP DIAGNOSTICS")
print("=" * 50)
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}...")

# Print ALL environment variables
print("\n🔍 ENVIRONMENT VARIABLES:")
env_vars = dict(os.environ)
for key, value in sorted(env_vars.items()):
    if key.startswith(('API', 'SUPABASE', 'PARSE', 'DB')):
        safe_value = value[:20] + '...' if len(value) > 20 else value
        print(f"  {key} = {safe_value}")

# Check if required vars exist
required = ['SUPABASE_URL', 'SUPABASE_KEY', 'API_HOST', 'API_PORT']
missing = [var for var in required if not os.environ.get(var)]

if missing:
    print(f"\n❌ MISSING VARIABLES: {missing}")
    print("💥 Cannot start without these variables!")
    sys.exit(1)
else:
    print(f"\n✅ All required variables present: {required}")

# Test basic Python imports
print("\n📦 TESTING BASIC IMPORTS:")
try:
    import asyncio
    print("✅ asyncio - OK")
    
    import uvicorn
    print("✅ uvicorn - OK")
    
    import logging
    print("✅ logging - OK")
    
except Exception as e:
    print(f"❌ Basic import failed: {e}")
    sys.exit(1)

# Test if we can see our files
print(f"\n📁 CHECKING FILES:")
files_to_check = ['src/main.py', 'src/api/routes.py', 'src/database/db_manager.py']
for file_path in files_to_check:
    if os.path.exists(file_path):
        print(f"✅ {file_path} - exists")
    else:
        print(f"❌ {file_path} - MISSING!")

# Try to add our paths
print(f"\n🛤️ SETTING UP PATHS:")
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)
print(f"Added to path: {current_dir}")
print(f"Added to path: {parent_dir}")

# Try ONE simple import from our code
print(f"\n🧪 TESTING OUR CODE IMPORT:")
try:
    # Just try to import the main file
    sys.path.append('/app/src')
    sys.path.append('/app')
    
    print("Trying to import src.main...")
    import src.main
    print("✅ src.main imported successfully!")
    
except Exception as e:
    print(f"❌ Failed to import src.main: {e}")
    print("Trying alternative import...")
    
    try:
        # Add src to path and try again
        import importlib.util
        spec = importlib.util.spec_from_file_location("main", "/app/src/main.py")
        if spec:
            main_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main_module)
            print("✅ main.py loaded via importlib!")
        else:
            print("❌ Could not create spec for main.py")
    except Exception as e2:
        print(f"❌ Alternative import also failed: {e2}")
        print("\n💥 CANNOT IMPORT OUR CODE - this is the problem!")
        
        # Show what files we can see
        print("\n📂 FILES IN /app:")
        try:
            for item in os.listdir('/app'):
                print(f"  {item}")
        except:
            print("  Cannot list /app directory")
            
        print("\n📂 FILES IN /app/src:")
        try:
            for item in os.listdir('/app/src'):
                print(f"  {item}")
        except:
            print("  Cannot list /app/src directory")
            
        sys.exit(1)

# If we got here, try to start the real app
print(f"\n🎯 STARTING REAL APPLICATION:")
try:
    # The main function is async, so we need to run it properly
    if hasattr(src.main, 'main'):
        print("Calling asyncio.run(src.main.main())...")
        import asyncio
        asyncio.run(src.main.main())
    else:
        print("❌ src.main has no main() function")
        print(f"Available in src.main: {dir(src.main)}")
        
except Exception as e:
    print(f"❌ Failed to start real application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
