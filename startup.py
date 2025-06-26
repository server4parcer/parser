#!/usr/bin/env python3
"""
Enhanced startup script for TimeWeb debugging
"""
import os
import sys
import logging

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check environment variables with detailed output"""
    logger.info("🔍 Checking environment variables...")
    
    # All possible variables
    all_vars = {
        'SUPABASE_URL': 'required',
        'SUPABASE_KEY': 'required', 
        'API_HOST': 'required',
        'API_PORT': 'required',
        'PARSE_URLS': 'required',
        'API_DEBUG': 'optional',
        'API_KEY': 'optional',
        'PARSE_INTERVAL': 'optional',
        'DB_HOST': 'conflicting',
        'DB_PASSWORD': 'conflicting',
        'DB_NAME': 'conflicting',
        'DB_PORT': 'conflicting',
        'DB_USER': 'conflicting'
    }
    
    missing_required = []
    conflicting_vars = []
    
    for var, status in all_vars.items():
        value = os.environ.get(var)
        if value:
            if status == 'conflicting':
                conflicting_vars.append(var)
                logger.warning(f"⚠️ {var}: {value[:20]}... (CONFLICTING - remove this)")
            else:
                safe_value = value[:20] + '...' if len(value) > 20 else value
                logger.info(f"✅ {var}: {safe_value}")
        else:
            if status == 'required':
                missing_required.append(var)
                logger.error(f"❌ {var}: MISSING (required)")
            else:
                logger.info(f"➖ {var}: not set ({status})")
    
    # Check for problems
    if missing_required:
        logger.error(f"💥 Missing required variables: {missing_required}")
        return False
    
    if conflicting_vars:
        logger.warning(f"⚠️ Found conflicting DB variables: {conflicting_vars}")
        logger.warning("⚠️ These may conflict with Supabase. Consider removing them.")
    
    logger.info("✅ All required environment variables present")
    return True

def test_imports():
    """Test imports step by step"""
    logger.info("📦 Testing imports...")
    
    try:
        # Add paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        sys.path.insert(0, parent_dir)
        sys.path.insert(0, current_dir)
        logger.info(f"📁 Added paths: {current_dir}, {parent_dir}")
        
        # Test basic imports
        logger.info("📦 Testing basic imports...")
        import asyncio
        logger.info("✅ asyncio imported")
        
        import uvicorn  
        logger.info("✅ uvicorn imported")
        
        # Test our modules
        logger.info("📦 Testing src modules...")
        
        from src.database.db_manager import DatabaseManager
        logger.info("✅ DatabaseManager imported")
        
        from src.api.routes import app
        logger.info("✅ API routes imported")
        
        from src.parser.yclients_parser import YClientsParser  
        logger.info("✅ YClientsParser imported")
        
        logger.info("✅ All imports successful")
        return True
        
    except Exception as e:
        logger.error(f"💥 Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """Test database connection"""
    logger.info("🗄️ Testing database connection...")
    
    try:
        from src.database.db_manager import DatabaseManager
        
        # Create manager but don't initialize yet
        db_manager = DatabaseManager()
        logger.info("✅ DatabaseManager created")
        
        # Check if we have Supabase or PostgreSQL config
        supabase_url = os.environ.get('SUPABASE_URL')
        db_host = os.environ.get('DB_HOST')
        
        if supabase_url:
            logger.info(f"🔗 Will use Supabase: {supabase_url[:30]}...")
        elif db_host:
            logger.info(f"🔗 Will use PostgreSQL: {db_host}")
        else:
            logger.warning("⚠️ No database configuration found")
            
        return True
        
    except Exception as e:
        logger.error(f"💥 Database test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main startup function with comprehensive checks"""
    logger.info("🚀 YClients Parser Enhanced Startup")
    logger.info("=" * 50)
    
    # Step 1: Environment check
    if not check_environment():
        logger.error("💥 Environment check failed!")
        sys.exit(1)
    
    logger.info("")
    
    # Step 2: Import check  
    if not test_imports():
        logger.error("💥 Import check failed!")
        sys.exit(1)
    
    logger.info("")
    
    # Step 3: Database check
    if not test_database_connection():
        logger.error("💥 Database check failed!")
        sys.exit(1)
    
    logger.info("")
    logger.info("🎯 All checks passed! Starting main application...")
    
    try:
        # Import and run main
        from src.main import main as app_main
        logger.info("📱 Calling main application...")
        app_main()
        
    except Exception as e:
        logger.error(f"💥 Application startup error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
