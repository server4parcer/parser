#!/usr/bin/env python3
"""
SUPER SIMPLE startup - runs lightweight parser without browser dependencies
"""
import os
import sys

print("=" * 50)
print("🚀 LIGHTWEIGHT PARSER STARTUP")
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

print("🎯 Starting lightweight parser (no browser dependencies)...")

try:
    # Run lightweight parser directly
    exec(open(os.path.join(current_dir, 'lightweight_parser.py')).read())
    
except Exception as e:
    print(f"💥 ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
