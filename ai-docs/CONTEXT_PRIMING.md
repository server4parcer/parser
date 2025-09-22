# YClients Parser - AI Agent Context Priming

**Essential Context for AI Coding Tools**  
*This document primes AI agents with critical project knowledge and current status*

---

## 🎯 **Project Identity**

**What This Is**: YClients booking data parser system that extracts sports venue booking information
**Platform**: Russian online booking platform (YClients.com) 
**Deployment**: TimeWeb VDS with Docker, Supabase database
**Language**: Python with FastAPI, Playwright/BeautifulSoup
**Current Status**: Database fixed, parsing needs major fixes

---

## 🚨 **CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION**

### **#1 Demo Data Fallback Problem** ⚠️ 
**File**: `lightweight_parser.py:91`
```python
# BROKEN - Returns fake tennis data instead of real parsing
except Exception as e:
    return self.generate_demo_data(url)  # ❌ WRONG!
```
**Impact**: System shows fake "Корт №1 Ультрапанорамик" data masking real failures
**Fix**: Replace with `return []` - no fake data ever

### **#2 No Automatic Scheduling** ⚠️
**Issue**: Parser only runs manually via `/parser/run` endpoint
**Missing**: Background `asyncio.create_task()` for 10-minute intervals
**File**: `lightweight_parser.py` main block needs background task

### **#3 Duration Not Extracted** ⚠️
**Issue**: Duration field hardcoded to 60 minutes in demo data
**Missing**: Real YClients duration parsing from page elements
**File**: `src/parser/production_data_extractor.py` needs duration extraction

---

## 📁 **Key File Locations**

### **Main Entry Points**
- `lightweight_parser.py` - Primary parser (has demo data problem)
- `src/main.py` - Full application entry point
- `src/parser/yclients_parser.py` - Playwright-based parser
- `src/database/db_manager.py` - Supabase integration (RLS fixed)

### **Configuration**
- `config/settings.py` - All system settings
- `CLAUDE.md` - Project instructions (already exists)
- Environment variables: `SUPABASE_URL`, `SUPABASE_KEY`, `PARSE_URLS`

### **Data Models**
- `src/database/models.py` - Database models with analytics fields
- Tables: `booking_data` (main), `urls` (URL management)

---

## 🔧 **Working Systems (Don't Break These)**

### **✅ Database Integration** 
- Supabase connection working
- RLS disabled via "nuclear fixes"
- Batch processing with fallback
- Data validation prevents time-as-price errors

### **✅ API Layer**
- FastAPI endpoints functional
- Authentication working
- Export capabilities (CSV/JSON)
- Diagnostic endpoints for debugging

### **✅ Data Models**
- Business analytics fields: court_type, time_category
- Location tracking: location_name, seat_number  
- Quality metadata: review_count, prepayment_required

---

## 🎨 **Architecture Patterns**

### **Parser Strategy**
- **Heavyweight**: Playwright + browser automation (`yclients_parser.py`)
- **Lightweight**: Requests + BeautifulSoup (`lightweight_parser.py`)
- **Production**: Optimized extractors with real selectors

### **Data Flow**
1. URL Input → Service Selection → Court Selection → Date Selection → Time Slots
2. Raw Extraction → Validation → Enhancement → Database Save
3. API Endpoints → Export → Client Consumption

### **Error Handling**
- Batch processing with individual fallback
- Comprehensive logging with diagnostic endpoints
- Nuclear database fixes for permissions
- Graceful degradation (no demo data fallbacks)

---

## 🚀 **Development Commands**

### **Running the System**
```bash
# Main application (API + parser)
python src/main.py

# Lightweight parser only  
python lightweight_parser.py

# Run tests
python tests/run_tests.py
```

### **Database Operations**
```bash
# Initialize database
python scripts/setup_db.py

# Test connection
python -c "from src.database.db_manager import DatabaseManager; import asyncio; asyncio.run(DatabaseManager().initialize())"
```

### **Monitoring**
```bash
# Health check
curl http://localhost:8000/health

# Parser status
curl http://localhost:8000/parser/status

# Diagnostic errors
curl http://localhost:8000/diagnostics/errors
```

---

## 🎯 **Current Focus Areas**

### **Immediate Priorities**
1. **Remove demo data fallback** from `lightweight_parser.py`
2. **Add background scheduling** with `asyncio.create_task()`
3. **Implement duration parsing** in data extractors
4. **Enhance YClients navigation** flow

### **Success Criteria**
- Zero demo data returned from any parser
- Automatic parsing every 10 minutes
- Real duration values (not hardcoded 60)
- >90% data accuracy for valid YClients URLs

---

## 📋 **Code Patterns & Conventions**

### **Logging Style**
```python
logger.info("✅ Success message")
logger.warning("⚠️ Warning message") 
logger.error("❌ Error message")
logger.info("🎯 Action starting...")
logger.info("📊 Data result: {...}")
```

### **Error Handling**
```python
try:
    # Operation
    logger.info("🎯 Starting operation...")
    result = await operation()
    logger.info("✅ Operation successful")
    return result
except Exception as e:
    logger.error(f"❌ Operation failed: {e}")
    return []  # ✅ Empty list, NOT demo data
```

### **Data Validation**
```python
# CRITICAL: Always validate price vs time
if self.is_time_format(price_value):
    logger.warning(f"⚠️ Time found as price: {price_value}")
    cleaned_price = "Цена не найдена"
```

---

## 🔍 **Debugging Quick Reference**

### **Common Issues**
- **Demo data appearing**: Check `generate_demo_data()` calls
- **Database saves failing**: Check RLS status, run diagnostics
- **No automatic parsing**: Check background task implementation
- **Duration always 60**: Check duration extraction methods

### **Diagnostic Commands**
```bash
# Check for demo data
curl http://localhost:8000/api/booking-data | grep "Корт №1"

# Verify background scheduling
tail -f logs/parser.log | grep "🔄 Starting scheduled parse"

# Test database saves
curl http://localhost:8000/diagnostics/test-save
```

---

## 🚨 **IMPORTANT CONTEXT FOR AI AGENTS**

### **What NOT to Do**
- ❌ Never add `generate_demo_data()` calls or return fake data
- ❌ Don't break existing Supabase integration (it's working)
- ❌ Don't add browser dependencies to lightweight parser
- ❌ Never store time values (10:00) as prices

### **What TO Do**  
- ✅ Return empty lists `[]` on parsing failures
- ✅ Add comprehensive logging with emoji indicators
- ✅ Implement background scheduling with asyncio
- ✅ Validate all data before database saves
- ✅ Use existing patterns and conventions

### **Architecture Awareness**
- This is a production system serving real business needs
- Database RLS issues were resolved with nuclear fixes
- Multiple parser implementations exist for different use cases
- System designed for 24/7 operation with monitoring

---

**📝 Remember**: This system extracts real business data from YClients booking platform. Quality and accuracy are critical. When in doubt, return empty results rather than fake data.