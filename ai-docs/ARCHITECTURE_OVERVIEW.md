# YClients Parser - Architecture Overview

**AI Agent Memory Document**  
*This document serves as persistent memory for AI coding tools working with the YClients parser codebase*

## 🏗️ System Architecture

### **Core Components**

1. **Parser Engine** (`src/parser/`)
   - **Main Parser**: `yclients_parser.py` - Playwright-based browser automation
   - **Lightweight Parser**: `lightweight_parser.py` - HTTP requests + BeautifulSoup
   - **Data Extractors**: Multiple versions for different extraction strategies
   - **Selectors**: Real YClients DOM selectors and patterns

2. **Database Layer** (`src/database/`)
   - **DatabaseManager**: `db_manager.py` - Supabase integration with RLS fix
   - **Models**: `models.py` - Data models with business analytics fields
   - **Queries**: SQL query builders and data operations

3. **API Layer** (`src/api/`)
   - **FastAPI Routes**: REST endpoints for data access
   - **Authentication**: API key authentication
   - **Data Export**: CSV/JSON export functionality

4. **Browser Management** (`src/browser/`)
   - **BrowserManager**: Playwright browser lifecycle
   - **ProxyManager**: Proxy rotation and management
   - **StealthConfig**: Anti-detection configurations

## 🎯 Key Business Logic

### **YClients Parsing Flow**
1. **Service Selection**: Handle service-type URLs (`record-type`)
2. **Court Selection**: Navigate through court/area selection
3. **Date Selection**: Extract available booking dates
4. **Time Slot Extraction**: Get available time slots with prices
5. **Data Validation**: Ensure price ≠ time format

### **Data Enhancement**
- **Court Type Detection**: Tennis, Basketball, Squash classification
- **Time Categorization**: DAY, EVENING, WEEKEND
- **Location Normalization**: Address and venue standardization
- **Price Validation**: Prevent time values being stored as prices

## 🔧 Configuration System

### **Environment Variables**
```bash
SUPABASE_URL=              # Supabase project URL
SUPABASE_KEY=              # Service role key (for RLS bypass)
PARSE_URLS=                # Comma-separated URLs to parse
API_KEY=                   # API authentication key
PARSE_INTERVAL=600         # Parse interval in seconds (10 min)
```

### **Key Settings** (`config/settings.py`)
- Parse interval: 600 seconds (10 minutes)
- Max retries: 3 attempts per URL
- Browser timeout: 30 seconds
- Page load timeout: 60 seconds
- Proxy rotation enabled

## 🗄️ Database Schema

### **Tables**
1. **booking_data**: Core booking information
   - Basic fields: date, time, price, provider
   - Analytics fields: court_type, time_category, duration
   - Location fields: location_name, seat_number
   - Metadata: review_count, prepayment_required

2. **urls**: Managed URL list for parsing
   - url, status, created_at, updated_at

### **Critical Data Integrity**
- **Price vs Time Validation**: Prevents "10:00" being stored as price
- **RLS Bypass**: Supabase Row Level Security disabled via service_role
- **Batch Processing**: 100 records per batch with individual fallback

## 🚨 Known Issues & Fixes

### **Demo Data Fallback Problem** ⚠️
- **Issue**: `lightweight_parser.py:91` returns fake tennis data on errors
- **Impact**: Masks real parsing failures with demo data
- **Fix**: Remove `generate_demo_data()` fallback, return empty list

### **Missing Automatic Scheduling** ⚠️
- **Issue**: No background task for 10-minute intervals
- **Current**: Manual parsing only via `/parser/run`
- **Fix**: Implement `asyncio.create_task(background_parser())`

### **Duration Not Extracted** ⚠️
- **Issue**: Duration field exists but hardcoded to 60 minutes
- **Fix**: Implement real duration parsing from YClients pages

## 🔀 Entry Points

### **Production Deployment**
- **Main**: `src/main.py` - Full application (API + parser)
- **Lightweight**: `lightweight_parser.py` - Simplified for TimeWeb
- **Super Simple**: `super_simple_startup.py` - Minimal production startup

### **Development & Testing**
- **Tests**: `tests/run_tests.py` - Comprehensive test suite
- **Scripts**: `scripts/` - Database setup and schema updates

## 🎨 Parser Variations

### **Multiple Parser Implementations**
1. **Full Parser** (`yclients_parser.py`): Playwright + full browser automation
2. **Lightweight** (`lightweight_parser.py`): Requests + BeautifulSoup
3. **Production** (`production_data_extractor.py`): Optimized for deployment

### **Data Extractor Evolution**
- **Basic**: Simple DOM parsing
- **Enhanced**: Business analytics fields
- **Fixed**: Price vs time validation
- **Production**: Robust error handling

## 🚀 Deployment Context

### **TimeWeb VDS Optimization**
- Lightweight requirements (no browser dependencies)
- Docker container support
- Health check endpoints
- Fallback configurations for missing dependencies

### **Development Tools Structure**
- **ai-docs/**: AI agent memory and context
- **specs/**: Detailed feature specifications and plans
- **.claude/**: Reusable prompt templates (if using Claude Code)

## 🔍 Context for AI Agents

### **When Working on Parser Issues**
1. Check `lightweight_parser.py` for demo data fallbacks
2. Verify real YClients DOM selectors in `selectors.py` files
3. Test price vs time validation in `db_manager.py`
4. Ensure Supabase RLS is disabled for saves to work

### **When Adding Features**
1. Update models in `src/database/models.py`
2. Add API endpoints in `src/api/routes.py`
3. Enhance data extraction in appropriate extractor
4. Update tests in `tests/` directory

### **When Debugging**
1. Check logs for Supabase permission errors
2. Verify environment variables are set
3. Test database connection with diagnostic endpoints
4. Use `/diagnostics/` endpoints for detailed error info

---

*This document is maintained as AI agent memory to provide persistent context across coding sessions*